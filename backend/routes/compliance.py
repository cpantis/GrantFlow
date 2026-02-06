from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
import uuid
from datetime import datetime, timezone
from middleware.auth_middleware import get_current_user
from services.ai_service import check_eligibility, validate_coherence, chat_navigator
from services.orchestrator_service import run_orchestrator_check

router = APIRouter(prefix="/api/compliance", tags=["compliance"])
db = None

def set_db(database):
    global db
    db = database

class EligibilityCheckRequest(BaseModel):
    project_id: str
    program_cerinte: Optional[dict] = None

class ValidateRequest(BaseModel):
    project_id: str

class NavigatorRequest(BaseModel):
    message: str
    project_id: Optional[str] = None

@router.post("/eligibility-check")
async def run_eligibility_check(req: EligibilityCheckRequest, current_user: dict = Depends(get_current_user)):
    project = await db.projects.find_one({"id": req.project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Proiect negăsit")
    org = await db.organizations.find_one({"id": project["organizatie_id"]}, {"_id": 0})
    if not org:
        raise HTTPException(status_code=404, detail="Organizație negăsită")
    firm_data = {
        "denumire": org["denumire"],
        "cui": org["cui"],
        "caen_principal": org.get("caen_principal"),
        "nr_angajati": org.get("nr_angajati"),
        "data_infiintare": org.get("data_infiintare"),
        "date_financiare": org.get("date_financiare"),
        "stare": org.get("stare")
    }
    program_info = req.program_cerinte or {
        "program": project["program_finantare"],
        "buget_maxim": 1000000,
        "eligibilitate_minim": "IMM activ, minim 1 an vechime, fără datorii restante"
    }
    result = await check_eligibility(firm_data, program_info)
    report = {
        "id": str(uuid.uuid4()),
        "project_id": req.project_id,
        "type": "eligibility",
        "result": result.get("result", ""),
        "success": result["success"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": current_user["user_id"]
    }
    await db.compliance_reports.insert_one(report)
    await db.projects.update_one({"id": req.project_id}, {
        "$set": {"eligibility_report": report["id"], "updated_at": datetime.now(timezone.utc).isoformat()}
    })
    report.pop("_id", None)
    return report

@router.post("/validate")
async def run_validation(req: ValidateRequest, current_user: dict = Depends(get_current_user)):
    project = await db.projects.find_one({"id": req.project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Proiect negăsit")
    docs = await db.documents.find({"project_id": req.project_id}, {"_id": 0}).to_list(50)
    doc_summaries = [{"id": d["id"], "tip": d["tip"], "status": d["status"], "filename": d["filename"]} for d in docs]
    result = await validate_coherence(doc_summaries, {
        "titlu": project["titlu"],
        "buget_estimat": project.get("buget_estimat"),
        "obiective": project.get("obiective"),
        "program": project.get("program_finantare")
    })
    report = {
        "id": str(uuid.uuid4()),
        "project_id": req.project_id,
        "type": "validation",
        "result": result.get("result", ""),
        "success": result["success"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": current_user["user_id"]
    }
    await db.compliance_reports.insert_one(report)
    report.pop("_id", None)
    return report

@router.post("/navigator")
async def navigator_chat(req: NavigatorRequest, current_user: dict = Depends(get_current_user)):
    context = {}
    if req.project_id:
        project = await db.projects.find_one({"id": req.project_id}, {"_id": 0})
        if project:
            context = {
                "titlu": project["titlu"],
                "stare": project["stare"],
                "program": project.get("program_finantare"),
                "buget": project.get("buget_estimat"),
                "blocaje": project.get("blocaje", [])
            }
    result = await chat_navigator(req.message, context)
    return {"response": result.get("result", "Nu am putut genera un răspuns."), "success": result["success"]}

@router.get("/reports/{project_id}")
async def get_reports(project_id: str, current_user: dict = Depends(get_current_user)):
    reports = await db.compliance_reports.find({"project_id": project_id}, {"_id": 0}).to_list(50)
    return reports

@router.post("/submission-ready/{project_id}")
async def check_submission_ready(project_id: str, current_user: dict = Depends(get_current_user)):
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Proiect negăsit")
    docs = await db.documents.find({"project_id": project_id}, {"_id": 0}).to_list(50)
    checks = []
    has_cerere = any(d["tip"] == "cerere_finantare" for d in docs)
    checks.append({"check": "Cerere finanțare", "passed": has_cerere})
    has_memoriu = any(d["tip"] == "memoriu" for d in docs)
    checks.append({"check": "Memoriu justificativ", "passed": has_memoriu})
    has_declaratie = any(d["tip"] == "declaratie" for d in docs)
    checks.append({"check": "Declarații", "passed": has_declaratie})
    all_signed = all(d["status"] in ["semnat", "aprobat"] for d in docs) if docs else False
    checks.append({"check": "Toate documentele semnate", "passed": all_signed})
    has_budget = project.get("buget_estimat", 0) > 0
    checks.append({"check": "Buget definit", "passed": has_budget})
    all_passed = all(c["passed"] for c in checks)
    status = "READY_FOR_SUBMISSION" if all_passed else "BLOCKED"
    return {"status": status, "checks": checks, "project_id": project_id}
