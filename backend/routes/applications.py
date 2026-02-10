"""Applications (Dosare) - Complete workflow routes"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
import uuid, os, json, zipfile, io
from datetime import datetime, timezone
from middleware.auth_middleware import get_current_user
from services.funding_service import (
    get_programs, get_measures, get_calls, get_call, get_templates, get_template,
    APPLICATION_STATES, APPLICATION_STATE_LABELS, APPLICATION_TRANSITIONS, DEFAULT_FOLDER_GROUPS
)
from services.ai_service import generate_document_section, validate_coherence, check_eligibility
from services.pdf_service import generate_pdf

router = APIRouter(prefix="/api/v2", tags=["applications"])
db = None

def set_db(database):
    global db
    db = database

# --- Catalog ---
@router.get("/programs")
async def list_programs():
    programs = get_programs()
    for p in programs:
        p["measures"] = get_measures(p["id"])
        for m in p["measures"]:
            m["calls"] = get_calls(m["id"])
    return programs

@router.get("/calls")
async def list_calls(status: Optional[str] = None):
    calls = get_calls()
    if status: calls = [c for c in calls if c["status"] == status]
    for c in calls:
        m = next((m for m in get_measures() if m["id"] == c["measure_id"]), {})
        p = next((p for p in get_programs() if p["id"] == m.get("program_id")), {})
        c["measure_name"] = m.get("name", "")
        c["measure_code"] = m.get("code", "")
        c["program_name"] = p.get("name", "")
    return calls

@router.get("/calls/{call_id}")
async def get_call_detail(call_id: str):
    c = get_call(call_id)
    if not c: raise HTTPException(404, "Sesiune negăsită")
    return c

@router.get("/templates")
async def list_templates():
    return get_templates()

@router.get("/states")
async def get_states():
    return {"states": APPLICATION_STATE_LABELS, "transitions": APPLICATION_TRANSITIONS, "order": APPLICATION_STATES}

# --- Applications (Dosare) ---
class CreateApplicationRequest(BaseModel):
    company_id: str
    call_id: str
    title: str
    description: Optional[str] = ""

class TransitionRequest(BaseModel):
    new_state: str
    reason: Optional[str] = ""

@router.post("/applications")
async def create_application(req: CreateApplicationRequest, current_user: dict = Depends(get_current_user)):
    call = get_call(req.call_id)
    if not call: raise HTTPException(400, "Sesiune invalidă")
    org = await db.organizations.find_one({"id": req.company_id}, {"_id": 0})
    if not org: raise HTTPException(404, "Firmă negăsită")

    app_id = str(uuid.uuid4())
    m = next((m for m in get_measures() if m["id"] == call["measure_id"]), {})
    p = next((p for p in get_programs() if p["id"] == m.get("program_id")), {})

    application = {
        "id": app_id, "title": req.title, "description": req.description,
        "company_id": req.company_id, "company_name": org["denumire"], "company_cui": org.get("cui"),
        "call_id": req.call_id, "call_name": call["name"], "call_code": call.get("code"),
        "measure_name": m.get("name"), "measure_code": m.get("code"),
        "program_name": p.get("name"),
        "status": "call_selected", "status_label": APPLICATION_STATE_LABELS["call_selected"],
        "history": [
            {"from": None, "to": "draft", "at": datetime.now(timezone.utc).isoformat(), "by": current_user["user_id"], "reason": "Dosar creat"},
            {"from": "draft", "to": "call_selected", "at": datetime.now(timezone.utc).isoformat(), "by": current_user["user_id"], "reason": f"Sesiune selectată: {call['name']}"}
        ],
        "guide_assets": [], "required_documents": [], "checklist_frozen": False,
        "folder_groups": DEFAULT_FOLDER_GROUPS,
        "documents": [], "drafts": [], "procurement": [],
        "budget_estimated": 0, "budget_approved": 0, "expenses_total": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "created_by": current_user["user_id"]
    }
    await db.applications.insert_one(application)
    await db.audit_log.insert_one({"id": str(uuid.uuid4()), "action": "application.created", "entity_type": "application", "entity_id": app_id, "user_id": current_user["user_id"], "details": {"title": req.title, "call": call["name"]}, "timestamp": datetime.now(timezone.utc).isoformat()})
    application.pop("_id", None)
    return application

@router.get("/applications")
async def list_applications(company_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    q = {}
    if company_id: q["company_id"] = company_id
    apps = await db.applications.find(q, {"_id": 0}).to_list(100)
    return apps

@router.get("/applications/{app_id}")
async def get_application(app_id: str, current_user: dict = Depends(get_current_user)):
    app = await db.applications.find_one({"id": app_id}, {"_id": 0})
    if not app: raise HTTPException(404, "Dosar negăsit")
    return app

@router.post("/applications/{app_id}/transition")
async def transition_application(app_id: str, req: TransitionRequest, current_user: dict = Depends(get_current_user)):
    app = await db.applications.find_one({"id": app_id}, {"_id": 0})
    if not app: raise HTTPException(404, "Dosar negăsit")
    current = app["status"]
    if req.new_state not in APPLICATION_TRANSITIONS.get(current, []):
        raise HTTPException(400, f"Tranziția {current} → {req.new_state} nu este permisă")
    entry = {"from": current, "to": req.new_state, "at": datetime.now(timezone.utc).isoformat(), "by": current_user["user_id"], "reason": req.reason or ""}
    await db.applications.update_one({"id": app_id}, {"$set": {"status": req.new_state, "status_label": APPLICATION_STATE_LABELS.get(req.new_state), "updated_at": datetime.now(timezone.utc).isoformat()}, "$push": {"history": entry}})
    await db.audit_log.insert_one({"id": str(uuid.uuid4()), "action": "application.transition", "entity_type": "application", "entity_id": app_id, "user_id": current_user["user_id"], "details": {"from": current, "to": req.new_state}, "timestamp": datetime.now(timezone.utc).isoformat()})
    return {"message": f"Dosar mutat: {APPLICATION_STATE_LABELS.get(req.new_state)}", "new_state": req.new_state}

# --- Guide & Annexes ---
@router.post("/applications/{app_id}/guide")
async def upload_guide(app_id: str, file: UploadFile = File(...), tip: str = Form("ghid"), current_user: dict = Depends(get_current_user)):
    upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "guides")
    os.makedirs(upload_dir, exist_ok=True)
    fid = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1] if file.filename else ""
    safe = f"{fid}{ext}"
    content = await file.read()
    with open(os.path.join(upload_dir, safe), "wb") as f: f.write(content)
    asset = {"id": fid, "filename": file.filename, "stored_name": safe, "file_size": len(content), "tip": tip, "uploaded_at": datetime.now(timezone.utc).isoformat(), "uploaded_by": current_user["user_id"]}
    await db.applications.update_one({"id": app_id}, {"$push": {"guide_assets": asset}, "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}})
    # Auto-transition to guide_ready if currently call_selected
    app = await db.applications.find_one({"id": app_id}, {"_id": 0})
    if app and app["status"] == "call_selected":
        await db.applications.update_one({"id": app_id}, {"$set": {"status": "guide_ready", "status_label": APPLICATION_STATE_LABELS["guide_ready"]}, "$push": {"history": {"from": "call_selected", "to": "guide_ready", "at": datetime.now(timezone.utc).isoformat(), "by": "system", "reason": "Ghid încărcat"}}})
    return asset

# --- Required Documents (Checklist) ---
class RequiredDocumentRequest(BaseModel):
    official_name: str
    required: bool = True
    folder_group: str = "depunere"
    guide_reference: Optional[str] = None

@router.post("/applications/{app_id}/required-docs")
async def add_required_doc(app_id: str, req: RequiredDocumentRequest, current_user: dict = Depends(get_current_user)):
    app = await db.applications.find_one({"id": app_id}, {"_id": 0})
    if not app: raise HTTPException(404)
    if app.get("checklist_frozen"): raise HTTPException(400, "Checklist-ul este înghețat")
    existing = app.get("required_documents", [])
    doc = {"id": str(uuid.uuid4()), "order_index": len(existing) + 1, "official_name": req.official_name, "required": req.required, "folder_group": req.folder_group, "guide_reference": req.guide_reference, "status": "missing"}
    await db.applications.update_one({"id": app_id}, {"$push": {"required_documents": doc}})
    return doc

@router.post("/applications/{app_id}/required-docs/propose")
async def propose_required_docs(app_id: str, current_user: dict = Depends(get_current_user)):
    """AI agent proposes required documents from guide."""
    app = await db.applications.find_one({"id": app_id}, {"_id": 0})
    if not app: raise HTTPException(404)
    guide_info = ", ".join([a["filename"] for a in app.get("guide_assets", [])])
    call = get_call(app.get("call_id", ""))
    prompt_data = {"call": call, "guide_files": guide_info, "program": app.get("program_name")}
    result = await generate_document_section(template="Lista documente obligatorii conform ghidului solicitantului", data=prompt_data, section="Extrage lista completă de documente cerute, cu folder și ordine")
    # Parse proposed docs
    return {"proposed_text": result.get("result", ""), "source": "AI Agent"}

@router.post("/applications/{app_id}/required-docs/freeze")
async def freeze_checklist(app_id: str, current_user: dict = Depends(get_current_user)):
    await db.applications.update_one({"id": app_id}, {"$set": {"checklist_frozen": True, "updated_at": datetime.now(timezone.utc).isoformat()}})
    return {"message": "Checklist înghețat"}

# --- Documents in folders ---
@router.post("/applications/{app_id}/documents")
async def upload_app_document(app_id: str, file: UploadFile = File(...), folder_group: str = Form("depunere"), required_doc_id: Optional[str] = Form(None), current_user: dict = Depends(get_current_user)):
    upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "app_docs")
    os.makedirs(upload_dir, exist_ok=True)
    did = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1] if file.filename else ""
    safe = f"{did}{ext}"
    content = await file.read()
    with open(os.path.join(upload_dir, safe), "wb") as f: f.write(content)
    doc = {"id": did, "filename": file.filename, "stored_name": safe, "file_size": len(content), "content_type": file.content_type, "folder_group": folder_group, "required_doc_id": required_doc_id, "status": "uploaded", "uploaded_at": datetime.now(timezone.utc).isoformat(), "uploaded_by": current_user["user_id"]}
    await db.applications.update_one({"id": app_id}, {"$push": {"documents": doc}})
    # Update required doc status
    if required_doc_id:
        await db.applications.update_one({"id": app_id, "required_documents.id": required_doc_id}, {"$set": {"required_documents.$.status": "uploaded"}})
    return doc

# --- Drafts ---
class GenerateDraftRequest(BaseModel):
    template_id: str
    section: Optional[str] = None

@router.post("/applications/{app_id}/drafts/generate")
async def generate_draft(app_id: str, req: GenerateDraftRequest, current_user: dict = Depends(get_current_user)):
    app = await db.applications.find_one({"id": app_id}, {"_id": 0})
    if not app: raise HTTPException(404)
    tpl = get_template(req.template_id)
    if not tpl: raise HTTPException(404, "Template negăsit")
    org = await db.organizations.find_one({"id": app.get("company_id")}, {"_id": 0})
    data = {
        "dosar": {"title": app["title"], "call": app.get("call_name"), "program": app.get("program_name"), "budget": app.get("budget_estimated")},
        "firma": {k: (org or {}).get(k) for k in ["denumire", "cui", "adresa", "judet", "forma_juridica", "nr_reg_com", "caen_principal", "nr_angajati", "data_infiintare"]}
    }
    section = req.section or ", ".join(tpl["sections"])
    # Get custom rules for redactor agent
    custom_rules = await db.agent_rules.find_one({"agent_id": "redactor", "user_id": current_user["user_id"]}, {"_id": 0})
    extra_rules = "\n".join(custom_rules.get("reguli", [])) if custom_rules else ""
    result = await generate_document_section(template=f"{tpl['label']}: {', '.join(tpl['sections'])}\n{extra_rules}", data=data, section=section)
    content_text = result.get("result", "")
    pdf_file = generate_pdf(tpl["label"], content_text, (org or {}).get("denumire", ""), app["title"])
    draft = {"id": str(uuid.uuid4()), "template_id": req.template_id, "template_label": tpl["label"], "content": content_text, "pdf_filename": pdf_file, "status": "draft", "version": 1, "created_at": datetime.now(timezone.utc).isoformat(), "created_by": current_user["user_id"], "applied_rules": (custom_rules.get("reguli", []) if custom_rules else [])}
    await db.applications.update_one({"id": app_id}, {"$push": {"drafts": draft}})
    # Also save as document in depunere folder
    gen_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "generated")
    doc_entry = {"id": str(uuid.uuid4()), "filename": f"{tpl['label']}.pdf", "stored_name": pdf_file, "file_size": os.path.getsize(os.path.join(gen_dir, pdf_file)), "content_type": "application/pdf", "folder_group": "depunere", "status": "uploaded", "uploaded_at": datetime.now(timezone.utc).isoformat(), "uploaded_by": current_user["user_id"], "draft_id": draft["id"]}
    await db.applications.update_one({"id": app_id}, {"$push": {"documents": doc_entry}})
    draft["pdf_url"] = f"/api/funding/drafts/download/{pdf_file}"
    # Agent run log
    await db.agent_runs.insert_one({"id": str(uuid.uuid4()), "agent_id": "redactor", "application_id": app_id, "action": "generate_draft", "input": {"template": tpl["label"]}, "output": {"draft_id": draft["id"]}, "applied_rules": draft.get("applied_rules", []), "timestamp": datetime.now(timezone.utc).isoformat(), "user_id": current_user["user_id"]})
    return draft

@router.get("/applications/{app_id}/drafts")
async def list_drafts(app_id: str, current_user: dict = Depends(get_current_user)):
    app = await db.applications.find_one({"id": app_id}, {"_id": 0, "drafts": 1})
    return app.get("drafts", []) if app else []

# --- Validation & Evaluation ---
@router.post("/applications/{app_id}/validate")
async def validate_application(app_id: str, current_user: dict = Depends(get_current_user)):
    app = await db.applications.find_one({"id": app_id}, {"_id": 0})
    if not app: raise HTTPException(404)
    org = await db.organizations.find_one({"id": app.get("company_id")}, {"_id": 0})
    req_docs = app.get("required_documents", [])
    uploaded = [d for d in app.get("documents", [])]
    custom_rules = await db.agent_rules.find_one({"agent_id": "validator", "user_id": current_user["user_id"]}, {"_id": 0})
    extra = "\n".join(custom_rules.get("reguli", [])) if custom_rules else ""
    result = await validate_coherence(
        documents=[{"name": d.get("official_name"), "status": d.get("status"), "required": d.get("required")} for d in req_docs],
        project_data={"title": app["title"], "call": app.get("call_name"), "program": app.get("program_name"), "company": (org or {}).get("denumire"), "documents_uploaded": len(uploaded), "documents_required": len(req_docs), "extra_rules": extra}
    )
    report = {"id": str(uuid.uuid4()), "type": "validation", "application_id": app_id, "result": result.get("result", ""), "created_at": datetime.now(timezone.utc).isoformat()}
    await db.compliance_reports.insert_one(report)
    await db.agent_runs.insert_one({"id": str(uuid.uuid4()), "agent_id": "validator", "application_id": app_id, "action": "validate", "applied_rules": (custom_rules.get("reguli", []) if custom_rules else []), "timestamp": datetime.now(timezone.utc).isoformat(), "user_id": current_user["user_id"]})
    report.pop("_id", None)
    return report

@router.post("/applications/{app_id}/evaluate")
async def evaluate_application(app_id: str, current_user: dict = Depends(get_current_user)):
    app = await db.applications.find_one({"id": app_id}, {"_id": 0})
    if not app: raise HTTPException(404)
    org = await db.organizations.find_one({"id": app.get("company_id")}, {"_id": 0})
    result = await check_eligibility(
        firm_data={k: (org or {}).get(k) for k in ["denumire", "cui", "caen_principal", "nr_angajati", "data_infiintare", "stare"]},
        program_info={"call": app.get("call_name"), "program": app.get("program_name"), "budget_max": app.get("budget_estimated")}
    )
    report = {"id": str(uuid.uuid4()), "type": "evaluation", "application_id": app_id, "result": result.get("result", ""), "created_at": datetime.now(timezone.utc).isoformat()}
    await db.compliance_reports.insert_one(report)
    report.pop("_id", None)
    return report

# --- ZIP Export ---
@router.get("/applications/{app_id}/export")
async def export_application_zip(app_id: str, current_user: dict = Depends(get_current_user)):
    app = await db.applications.find_one({"id": app_id}, {"_id": 0})
    if not app: raise HTTPException(404)
    zip_buffer = io.BytesIO()
    base_dirs = [
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "app_docs"),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "generated"),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "guides"),
    ]
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        manifest = {"application": app["title"], "company": app.get("company_name"), "call": app.get("call_name"), "exported_at": datetime.now(timezone.utc).isoformat(), "files": []}
        for doc in app.get("documents", []):
            folder = doc.get("folder_group", "depunere")
            folder_name = next((fg["name"] for fg in app.get("folder_groups", DEFAULT_FOLDER_GROUPS) if fg["key"] == folder), f"99_{folder}")
            fname = doc.get("filename", doc.get("stored_name"))
            # Find file
            for bd in base_dirs:
                fpath = os.path.join(bd, doc.get("stored_name", ""))
                if os.path.exists(fpath):
                    zf.write(fpath, f"{folder_name}/{fname}")
                    manifest["files"].append({"folder": folder_name, "filename": fname, "status": doc.get("status")})
                    break
        # Add guide assets
        for ga in app.get("guide_assets", []):
            for bd in base_dirs:
                fpath = os.path.join(bd, ga.get("stored_name", ""))
                if os.path.exists(fpath):
                    zf.write(fpath, f"00_Ghid/{ga['filename']}")
                    break
        zf.writestr("manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))
    zip_buffer.seek(0)
    zip_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", f"export_{app_id}.zip")
    with open(zip_path, "wb") as f: f.write(zip_buffer.getvalue())
    return FileResponse(zip_path, media_type="application/zip", filename=f"Dosar_{app.get('call_code','')}.zip")
