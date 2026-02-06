from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
import uuid
import os
from datetime import datetime, timezone
from middleware.auth_middleware import get_current_user
from services.funding_service import (
    get_programs, get_program, get_masura, get_sesiune,
    search_sicap, search_afir_preturi, get_project_types,
    get_draft_templates, get_draft_template
)
from services.ai_service import check_eligibility, generate_document_section, validate_coherence
from services.pdf_service import generate_pdf

router = APIRouter(prefix="/api/funding", tags=["funding"])
db = None

def set_db(database):
    global db
    db = database

class SetProjectConfigRequest(BaseModel):
    project_id: str
    sesiune_id: Optional[str] = None
    tip_proiect: Optional[str] = None
    locatie_implementare: Optional[str] = None
    judet_implementare: Optional[str] = None
    tema_proiect: Optional[str] = None
    achizitii: Optional[List[dict]] = None

class AddLegislationRequest(BaseModel):
    project_id: str
    titlu: str
    tip: str  # ghid, procedura_evaluare, regulament, altele
    continut: Optional[str] = None

class GenerateDraftRequest(BaseModel):
    project_id: str
    template_id: str
    sectiune: Optional[str] = None

class EvaluateConformityRequest(BaseModel):
    project_id: str

# === Programs / Measures / Sessions ===

@router.get("/programs")
async def list_programs():
    return get_programs()

@router.get("/programs/{program_id}")
async def get_program_detail(program_id: str):
    p = get_program(program_id)
    if not p:
        raise HTTPException(status_code=404, detail="Program negăsit")
    return p

@router.get("/masuri/{masura_id}")
async def get_masura_detail(masura_id: str):
    m = get_masura(masura_id)
    if not m:
        raise HTTPException(status_code=404, detail="Măsură negăsită")
    return m

@router.get("/sesiuni/{sesiune_id}")
async def get_sesiune_detail(sesiune_id: str):
    s = get_sesiune(sesiune_id)
    if not s:
        raise HTTPException(status_code=404, detail="Sesiune negăsită")
    return s

# === SICAP & AFIR Search ===

@router.get("/sicap/search")
async def sicap_search(q: str):
    if len(q) < 2:
        raise HTTPException(status_code=400, detail="Minim 2 caractere")
    return search_sicap(q)

@router.get("/afir/preturi")
async def afir_preturi_search(q: str):
    if len(q) < 2:
        raise HTTPException(status_code=400, detail="Minim 2 caractere")
    return search_afir_preturi(q)

# === Project Types & Templates ===

@router.get("/project-types")
async def list_project_types():
    return get_project_types()

@router.get("/templates")
async def list_templates():
    return get_draft_templates()

@router.get("/templates/{template_id}")
async def get_template(template_id: str):
    t = get_draft_template(template_id)
    if not t:
        raise HTTPException(status_code=404, detail="Template negăsit")
    return t

# === Project Configuration ===

@router.post("/project-config")
async def set_project_config(req: SetProjectConfigRequest, current_user: dict = Depends(get_current_user)):
    project = await db.projects.find_one({"id": req.project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Proiect negăsit")

    update = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if req.sesiune_id:
        sesiune = get_sesiune(req.sesiune_id)
        if sesiune:
            update["sesiune"] = sesiune
            update["program_finantare"] = sesiune["program_denumire"]
            update["masura"] = {"id": sesiune["masura_id"], "cod": sesiune["masura_cod"], "denumire": sesiune["masura_denumire"]}
    if req.tip_proiect:
        update["tip_proiect"] = req.tip_proiect
    if req.locatie_implementare:
        update["locatie_implementare"] = req.locatie_implementare
    if req.judet_implementare:
        update["judet_implementare"] = req.judet_implementare
    if req.tema_proiect:
        update["tema_proiect"] = req.tema_proiect
    if req.achizitii is not None:
        update["achizitii"] = req.achizitii

    await db.projects.update_one({"id": req.project_id}, {"$set": update})
    project = await db.projects.find_one({"id": req.project_id}, {"_id": 0})
    return project

# === Legislation ===

@router.post("/legislation")
async def add_legislation(req: AddLegislationRequest, current_user: dict = Depends(get_current_user)):
    leg_id = str(uuid.uuid4())
    leg = {
        "id": leg_id,
        "project_id": req.project_id,
        "titlu": req.titlu,
        "tip": req.tip,
        "continut": req.continut or "",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": current_user["user_id"]
    }
    await db.legislation.insert_one(leg)
    await db.projects.update_one({"id": req.project_id}, {"$push": {"legislation_ids": leg_id}})
    leg.pop("_id", None)
    return leg

@router.post("/legislation/upload")
async def upload_legislation(
    file: UploadFile = File(...),
    project_id: str = Form(...),
    titlu: str = Form(...),
    tip: str = Form("ghid"),
    current_user: dict = Depends(get_current_user)
):
    import os
    upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "legislation")
    os.makedirs(upload_dir, exist_ok=True)
    leg_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1] if file.filename else ""
    safe_name = f"{leg_id}{ext}"
    file_path = os.path.join(upload_dir, safe_name)
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    leg = {
        "id": leg_id,
        "project_id": project_id,
        "titlu": titlu,
        "tip": tip,
        "filename": file.filename,
        "stored_name": safe_name,
        "file_size": len(content),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": current_user["user_id"]
    }
    await db.legislation.insert_one(leg)
    await db.projects.update_one({"id": project_id}, {"$push": {"legislation_ids": leg_id}})
    leg.pop("_id", None)
    return leg

@router.get("/legislation/{project_id}")
async def list_legislation(project_id: str, current_user: dict = Depends(get_current_user)):
    legs = await db.legislation.find({"project_id": project_id}, {"_id": 0}).to_list(50)
    return legs

# === Draft Generation ===

@router.post("/generate-draft")
async def generate_draft(req: GenerateDraftRequest, current_user: dict = Depends(get_current_user)):
    project = await db.projects.find_one({"id": req.project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Proiect negăsit")
    template = get_draft_template(req.template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template negăsit")

    org = await db.organizations.find_one({"id": project.get("organizatie_id")}, {"_id": 0})
    data = {
        "proiect": {k: project.get(k) for k in ["titlu", "descriere", "buget_estimat", "program_finantare", "tip_proiect", "tema_proiect", "obiective", "achizitii", "locatie_implementare"]},
        "firma": {k: (org or {}).get(k) for k in ["denumire", "cui", "adresa", "judet", "forma_juridica", "nr_reg_com", "caen_principal", "nr_angajati", "data_infiintare"]}
    }

    section = req.sectiune or ", ".join(template["sectiuni"])
    result = await generate_document_section(
        template=f"Document: {template['label']}, Secțiuni: {', '.join(template['sectiuni'])}",
        data=data,
        section=section
    )

    draft_id = str(uuid.uuid4())
    draft = {
        "id": draft_id,
        "project_id": req.project_id,
        "template_id": req.template_id,
        "template_label": template["label"],
        "sectiune": section,
        "continut": result.get("result", ""),
        "status": "draft",
        "versiune": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": current_user["user_id"]
    }
    await db.drafts.insert_one(draft)
    draft.pop("_id", None)
    return draft

@router.get("/drafts/{project_id}")
async def list_drafts(project_id: str, current_user: dict = Depends(get_current_user)):
    drafts = await db.drafts.find({"project_id": project_id}, {"_id": 0}).to_list(50)
    return drafts

# === Conformity Evaluation Agent ===

@router.post("/evaluate-conformity")
async def evaluate_conformity(req: EvaluateConformityRequest, current_user: dict = Depends(get_current_user)):
    project = await db.projects.find_one({"id": req.project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Proiect negăsit")

    org = await db.organizations.find_one({"id": project.get("organizatie_id")}, {"_id": 0})
    docs = await db.documents.find({"project_id": req.project_id}, {"_id": 0}).to_list(50)
    drafts = await db.drafts.find({"project_id": req.project_id}, {"_id": 0}).to_list(50)
    legs = await db.legislation.find({"project_id": req.project_id}, {"_id": 0}).to_list(20)

    doc_list = [{"tip": d.get("tip"), "status": d.get("status"), "filename": d.get("filename")} for d in docs]
    draft_list = [{"template": d.get("template_label"), "status": d.get("status")} for d in drafts]

    result = await validate_coherence(
        documents=doc_list + draft_list,
        project_data={
            "titlu": project.get("titlu"),
            "program": project.get("program_finantare"),
            "masura": project.get("masura", {}),
            "tip_proiect": project.get("tip_proiect"),
            "buget": project.get("buget_estimat"),
            "obiective": project.get("obiective"),
            "achizitii": project.get("achizitii", []),
            "firma": {"denumire": (org or {}).get("denumire"), "cui": (org or {}).get("cui")},
            "legislatie_incarcata": len(legs),
            "documente_incarcate": len(docs),
            "drafturi_generate": len(drafts)
        }
    )

    report = {
        "id": str(uuid.uuid4()),
        "project_id": req.project_id,
        "type": "conformity_grid",
        "result": result.get("result", ""),
        "success": result["success"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": current_user["user_id"]
    }
    await db.compliance_reports.insert_one(report)
    report.pop("_id", None)
    return report
