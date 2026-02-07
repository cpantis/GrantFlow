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


@router.post("/manual")
async def create_organization_manual(
    onrc_file: UploadFile = File(...),
    ci_file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Create organization by uploading ONRC + CI. Agents handle OCR → extract → validate → store."""
    upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "onrc")
    os.makedirs(upload_dir, exist_ok=True)

    # Save ONRC document
    onrc_id = str(uuid.uuid4())
    onrc_ext = os.path.splitext(onrc_file.filename)[1] if onrc_file.filename else ""
    onrc_safe = f"{onrc_id}{onrc_ext}"
    onrc_content = await onrc_file.read()
    with open(os.path.join(upload_dir, onrc_safe), "wb") as f:
        f.write(onrc_content)

    # Save CI document
    ci_id = str(uuid.uuid4())
    ci_ext = os.path.splitext(ci_file.filename)[1] if ci_file.filename else ""
    ci_safe = f"{ci_id}{ci_ext}"
    ci_content = await ci_file.read()
    with open(os.path.join(upload_dir, ci_safe), "wb") as f:
        f.write(ci_content)

    # Agent Parser: OCR both documents
    onrc_ocr = await process_ocr(onrc_id, "certificat", onrc_file.filename, db)
    ci_ocr = await process_ocr(ci_id, "ci", ci_file.filename, db)

    # Agent Colector: Extract firm data from OCR results
    onrc_fields = onrc_ocr.get("extracted_fields", {})
    ci_fields = ci_ocr.get("extracted_fields", {})

    # Derive firm data from OCR
    cui_extracted = onrc_fields.get("cui_firma", onrc_fields.get("cui", ""))
    denumire_extracted = onrc_fields.get("denumire_firma", onrc_fields.get("denumire", ""))
    admin_name = ci_fields.get("nume", "") + " " + ci_fields.get("prenume", "")

    # Validate: check CUI not empty
    if not cui_extracted:
        cui_extracted = "NECUNOSCUT"

    existing = await db.organizations.find_one({"cui": cui_extracted})
    if existing and cui_extracted != "NECUNOSCUT":
        raise HTTPException(status_code=400, detail=f"Firma cu CUI {cui_extracted} există deja")

    org_id = str(uuid.uuid4())
    org_doc = {
        "id": org_id,
        "cui": cui_extracted,
        "denumire": denumire_extracted or "Firmă din documente",
        "forma_juridica": _detect_forma(denumire_extracted),
        "nr_reg_com": onrc_fields.get("numar_contract", onrc_fields.get("nr_reg_com", "")),
        "adresa": onrc_fields.get("adresa", ci_fields.get("adresa", "")),
        "cod_postal": "",
        "judet": onrc_fields.get("judet", ""),
        "localitate": onrc_fields.get("localitate", ""),
        "stare": "ACTIVA",
        "stare_detalii": "Extras automat din documente (OCR)",
        "data_infiintare": onrc_fields.get("data_infiintare", ""),
        "telefon": onrc_fields.get("telefon", None),
        "tva": None,
        "tva_la_incasare": [],
        "capital_social": None,
        "caen_principal": None,
        "caen_secundare": [],
        "administratori": [{"nume": admin_name.strip(), "functie": "Administrator", "sursa": "CI OCR"}] if admin_name.strip() else [],
        "asociati": [],
        "nr_angajati": None,
        "radiata": False,
        "certificat_constatator": None,
        "date_financiare": None,
        "sursa_date": "Upload ONRC + CI (OCR automat)",
        "onrc_document": {
            "id": onrc_id, "filename": onrc_file.filename, "stored_name": onrc_safe,
            "file_size": len(onrc_content), "content_type": onrc_file.content_type,
            "ocr_status": onrc_ocr.get("status"), "ocr_confidence": onrc_ocr.get("overall_confidence"),
            "uploaded_at": datetime.now(timezone.utc).isoformat()
        },
        "ci_document": {
            "id": ci_id, "filename": ci_file.filename, "stored_name": ci_safe,
            "file_size": len(ci_content), "content_type": ci_file.content_type,
            "ocr_status": ci_ocr.get("status"), "ocr_confidence": ci_ocr.get("overall_confidence"),
            "uploaded_at": datetime.now(timezone.utc).isoformat()
        },
        "ocr_results": {
            "onrc": onrc_ocr,
            "ci": ci_ocr
        },
        "needs_review": onrc_ocr.get("needs_human_review", False) or ci_ocr.get("needs_human_review", False),
        "meta_actualizare": {},
        "members": [{
            "user_id": current_user["user_id"],
            "email": current_user["email"],
            "rol": "owner",
            "added_at": datetime.now(timezone.utc).isoformat()
        }],
        "authorizations": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "created_by": current_user["user_id"]
    }
    await db.organizations.insert_one(org_doc)

    # Store documents in documents collection too
    for doc_info, doc_type in [({"id": onrc_id, "filename": onrc_file.filename, "stored_name": onrc_safe, "size": len(onrc_content), "ct": onrc_file.content_type, "ocr": onrc_ocr}, "certificat"),
                                ({"id": ci_id, "filename": ci_file.filename, "stored_name": ci_safe, "size": len(ci_content), "ct": ci_file.content_type, "ocr": ci_ocr}, "ci")]:
        await db.documents.insert_one({
            "id": doc_info["id"], "filename": doc_info["filename"], "stored_name": doc_info["stored_name"],
            "file_size": doc_info["size"], "content_type": doc_info["ct"],
            "organizatie_id": org_id, "project_id": None,
            "tip": doc_type, "faza": None, "status": "draft",
            "descriere": f"Upload automat - {'ONRC' if doc_type == 'certificat' else 'CI'}",
            "versiune": 1,
            "versions": [{"versiune": 1, "filename": doc_info["filename"], "stored_name": doc_info["stored_name"], "file_size": doc_info["size"], "uploaded_at": datetime.now(timezone.utc).isoformat(), "uploaded_by": current_user["user_id"]}],
            "ocr_status": doc_info["ocr"].get("status", "pending"),
            "ocr_data": doc_info["ocr"], "tags": ["upload_manual"],
            "created_at": datetime.now(timezone.utc).isoformat(), "updated_at": datetime.now(timezone.utc).isoformat(), "created_by": current_user["user_id"]
        })

    await db.audit_log.insert_one({
        "id": str(uuid.uuid4()),
        "action": "organization.created_from_documents",
        "entity_type": "organization",
        "entity_id": org_id,
        "user_id": current_user["user_id"],
        "details": {
            "cui_extracted": cui_extracted,
            "denumire_extracted": denumire_extracted,
            "onrc_confidence": onrc_ocr.get("overall_confidence"),
            "ci_confidence": ci_ocr.get("overall_confidence"),
            "needs_review": org_doc["needs_review"]
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    org_doc.pop("_id", None)
    return org_doc


def _detect_forma(denumire: str) -> str:
    d = (denumire or "").upper()
    if "S.R.L" in d or "SRL" in d: return "SRL"
    if "S.A." in d or " SA" in d: return "SA"
    if "PFA" in d: return "PFA"
    if "I.I." in d: return "II"
    return "SRL"

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
