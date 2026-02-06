from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
import uuid
from datetime import datetime, timezone
from middleware.auth_middleware import get_current_user
from services.onrc_service import lookup_cui, get_certificat_constatator
from services.anaf_service import get_financial_data, get_financial_history, check_obligatii_restante

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
    existing = await db.organizations.find_one({"cui": req.cui})
    if existing:
        raise HTTPException(status_code=400, detail="Organizația cu acest CUI există deja")
    onrc_data = await lookup_cui(req.cui)
    if not onrc_data["success"]:
        raise HTTPException(status_code=400, detail="CUI invalid sau indisponibil")
    cert = await get_certificat_constatator(req.cui)
    financial = await get_financial_data(req.cui)
    org_id = str(uuid.uuid4())
    org_doc = {
        "id": org_id,
        "cui": req.cui,
        "denumire": onrc_data["data"]["denumire"],
        "forma_juridica": onrc_data["data"]["forma_juridica"],
        "nr_reg_com": onrc_data["data"]["nr_reg_com"],
        "adresa": onrc_data["data"]["adresa"],
        "judet": onrc_data["data"]["judet"],
        "stare": onrc_data["data"]["stare"],
        "data_infiintare": onrc_data["data"]["data_infiintare"],
        "capital_social": onrc_data["data"]["capital_social"],
        "caen_principal": onrc_data["data"]["caen_principal"],
        "caen_secundare": onrc_data["data"]["caen_secundare"],
        "administratori": onrc_data["data"]["administratori"],
        "asociati": onrc_data["data"]["asociati"],
        "nr_angajati": onrc_data["data"]["nr_angajati"],
        "certificat_constatator": cert.get("certificat"),
        "date_financiare": financial.get("data"),
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
        "details": {"cui": req.cui, "denumire": org_doc["denumire"]},
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
    is_member = any(m["user_id"] == current_user["user_id"] for m in org.get("members", []))
    if not is_member:
        raise HTTPException(status_code=403, detail="Acces interzis")
    return org

@router.post("/{org_id}/members")
async def add_member(org_id: str, req: AddMemberRequest, current_user: dict = Depends(get_current_user)):
    org = await db.organizations.find_one({"id": org_id}, {"_id": 0})
    if not org:
        raise HTTPException(status_code=404, detail="Organizație negăsită")
    is_owner = any(m["user_id"] == current_user["user_id"] and m["rol"] == "owner" for m in org.get("members", []))
    if not is_owner:
        raise HTTPException(status_code=403, detail="Doar owner-ul poate adăuga membri")
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
