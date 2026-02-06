from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import Optional, List
import uuid
import os
from datetime import datetime, timezone
from middleware.auth_middleware import get_current_user, require_org_permission
from services.onrc_service import lookup_cui, get_certificat_constatator
from services.anaf_service import get_financial_data, get_financial_history, check_obligatii_restante
from services.ocr_service import process_ocr

router = APIRouter(prefix="/api/organizations", tags=["organizations"])
db = None

def set_db(database):
    global db
    db = database

class CreateOrgRequest(BaseModel):
    cui: str

class AddMemberRequest(BaseModel):
    email: str
    rol: str = "imputernicit"

class CreateAuthorizationRequest(BaseModel):
    user_id: str
    scope: List[str]
    valabil_pana: str
    observatii: Optional[str] = None

@router.post("")
async def create_organization(req: CreateOrgRequest, current_user: dict = Depends(get_current_user)):
    cui_clean = req.cui.strip().replace("RO", "").replace("ro", "").strip()
    existing = await db.organizations.find_one({"cui": cui_clean})
    if existing:
        raise HTTPException(status_code=400, detail="Firma cu acest CUI există deja în platformă")
    onrc_data = await lookup_cui(cui_clean)
    if not onrc_data["success"]:
        detail = onrc_data.get("error", "CUI invalid sau indisponibil")
        raise HTTPException(status_code=400, detail=detail)
    d = onrc_data["data"]
    cert = await get_certificat_constatator(cui_clean)
    financial = await get_financial_data(cui_clean)
    org_id = str(uuid.uuid4())
    org_doc = {
        "id": org_id,
        "cui": d.get("cui", cui_clean),
        "denumire": d.get("denumire", ""),
        "forma_juridica": d.get("forma_juridica", ""),
        "nr_reg_com": d.get("nr_reg_com", ""),
        "adresa": d.get("adresa", ""),
        "cod_postal": d.get("cod_postal", ""),
        "judet": d.get("judet", ""),
        "localitate": d.get("localitate", ""),
        "stare": d.get("stare", "NECUNOSCUT"),
        "stare_detalii": d.get("stare_detalii", ""),
        "data_infiintare": d.get("data_infiintare", ""),
        "telefon": d.get("telefon"),
        "tva": d.get("tva"),
        "tva_la_incasare": d.get("tva_la_incasare", []),
        "capital_social": d.get("capital_social"),
        "caen_principal": d.get("caen_principal"),
        "caen_secundare": d.get("caen_secundare", []),
        "administratori": d.get("administratori", []),
        "asociati": d.get("asociati", []),
        "nr_angajati": d.get("nr_angajati"),
        "radiata": d.get("radiata", False),
        "certificat_constatator": cert.get("certificat"),
        "date_financiare": financial.get("data"),
        "sursa_date": d.get("sursa", "OpenAPI.ro"),
        "meta_actualizare": d.get("meta", {}),
        "members": [
            {
                "user_id": current_user["user_id"],
                "email": current_user["email"],
                "rol": "owner",
                "added_at": datetime.now(timezone.utc).isoformat()
            }
        ],
        "authorizations": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "created_by": current_user["user_id"]
    }
    await db.organizations.insert_one(org_doc)
    await db.audit_log.insert_one({
        "id": str(uuid.uuid4()),
        "action": "organization.created",
        "entity_type": "organization",
        "entity_id": org_id,
        "user_id": current_user["user_id"],
        "details": {"cui": cui_clean, "denumire": org_doc["denumire"], "sursa": "OpenAPI.ro"},
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    org_doc.pop("_id", None)
    return org_doc

@router.get("")
async def list_organizations(current_user: dict = Depends(get_current_user)):
    orgs = await db.organizations.find(
        {"members.user_id": current_user["user_id"]}, {"_id": 0}
    ).to_list(100)
    return orgs

@router.get("/{org_id}")
async def get_organization(org_id: str, current_user: dict = Depends(get_current_user)):
    org = await db.organizations.find_one({"id": org_id}, {"_id": 0})
    if not org:
        raise HTTPException(status_code=404, detail="Organizație negăsită")
    role_info = await require_org_permission(current_user["user_id"], org_id, "read")
    # Consultants get limited view - no financial data
    if role_info["role"] == "consultant":
        org.pop("date_financiare", None)
        org.pop("certificat_constatator", None)
        org.pop("authorizations", None)
    return org

@router.post("/{org_id}/members")
async def add_member(org_id: str, req: AddMemberRequest, current_user: dict = Depends(get_current_user)):
    await require_org_permission(current_user["user_id"], org_id, "manage_members")
    org = await db.organizations.find_one({"id": org_id}, {"_id": 0})
    if not org:
        raise HTTPException(status_code=404, detail="Organizație negăsită")
    target_user = await db.users.find_one({"email": req.email}, {"_id": 0, "password_hash": 0})
    if not target_user:
        raise HTTPException(status_code=404, detail="Utilizatorul nu există")
    already_member = any(m["email"] == req.email for m in org.get("members", []))
    if already_member:
        raise HTTPException(status_code=400, detail="Utilizatorul este deja membru")
    new_member = {
        "user_id": target_user["id"],
        "email": req.email,
        "rol": req.rol,
        "added_at": datetime.now(timezone.utc).isoformat()
    }
    await db.organizations.update_one({"id": org_id}, {"$push": {"members": new_member}})
    await db.audit_log.insert_one({
        "id": str(uuid.uuid4()),
        "action": "organization.member_added",
        "entity_type": "organization",
        "entity_id": org_id,
        "user_id": current_user["user_id"],
        "details": {"member_email": req.email, "rol": req.rol},
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    return {"message": "Membru adăugat cu succes", "member": new_member}

@router.post("/{org_id}/authorizations")
async def create_authorization(org_id: str, req: CreateAuthorizationRequest, current_user: dict = Depends(get_current_user)):
    await require_org_permission(current_user["user_id"], org_id, "manage_authorizations")
    org = await db.organizations.find_one({"id": org_id}, {"_id": 0})
    if not org:
        raise HTTPException(status_code=404, detail="Organizație negăsită")
    auth_id = str(uuid.uuid4())
    authorization = {
        "id": auth_id,
        "user_id": req.user_id,
        "scope": req.scope,
        "valabil_pana": req.valabil_pana,
        "observatii": req.observatii,
        "status": "activa",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": current_user["user_id"]
    }
    await db.organizations.update_one({"id": org_id}, {"$push": {"authorizations": authorization}})
    return {"message": "Împuternicire creată", "authorization": authorization}

@router.get("/{org_id}/financial")
async def get_org_financial(org_id: str, current_user: dict = Depends(get_current_user)):
    org = await db.organizations.find_one({"id": org_id}, {"_id": 0})
    if not org:
        raise HTTPException(status_code=404, detail="Organizație negăsită")
    history = await get_financial_history(org["cui"])
    debts = await check_obligatii_restante(org["cui"])
    return {"financial_history": history["data"], "obligatii_restante": debts["data"]}

@router.post("/{org_id}/refresh-onrc")
async def refresh_onrc(org_id: str, current_user: dict = Depends(get_current_user)):
    org = await db.organizations.find_one({"id": org_id}, {"_id": 0})
    if not org:
        raise HTTPException(status_code=404, detail="Organizație negăsită")
    onrc_data = await lookup_cui(org["cui"])
    cert = await get_certificat_constatator(org["cui"])
    await db.organizations.update_one({"id": org_id}, {"$set": {
        "administratori": onrc_data["data"]["administratori"],
        "certificat_constatator": cert.get("certificat"),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }})
    return {"message": "Date ONRC actualizate", "data": onrc_data["data"]}


@router.delete("/{org_id}")
async def delete_organization(org_id: str, current_user: dict = Depends(get_current_user)):
    await require_org_permission(current_user["user_id"], org_id, "delete")
    org = await db.organizations.find_one({"id": org_id}, {"_id": 0})
    if not org:
        raise HTTPException(status_code=404, detail="Firma negăsită")
    # Check no active projects
    active_projects = await db.projects.count_documents({"organizatie_id": org_id, "stare": {"$nin": ["arhivat", "respins"]}})
    if active_projects > 0:
        raise HTTPException(status_code=400, detail=f"Nu se poate șterge firma. Există {active_projects} proiecte active asociate.")
    await db.organizations.delete_one({"id": org_id})
    await db.audit_log.insert_one({
        "id": str(uuid.uuid4()),
        "action": "organization.deleted",
        "entity_type": "organization",
        "entity_id": org_id,
        "user_id": current_user["user_id"],
        "details": {"cui": org["cui"], "denumire": org["denumire"]},
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    return {"message": f"Firma '{org['denumire']}' a fost ștearsă"}
