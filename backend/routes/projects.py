from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import uuid
from datetime import datetime, timezone
from middleware.auth_middleware import get_current_user, require_org_permission, require_project_permission

router = APIRouter(prefix="/api/projects", tags=["projects"])
db = None

def set_db(database):
    global db
    db = database

VALID_STATES = [
    "draft", "pre_eligibil", "blocat", "conform", "depus",
    "aprobat", "respins", "in_implementare", "suspendat",
    "finalizat", "audit_post", "arhivat"
]

VALID_TRANSITIONS = {
    "draft": ["pre_eligibil", "blocat"],
    "pre_eligibil": ["blocat", "conform"],
    "blocat": ["draft", "pre_eligibil"],
    "conform": ["depus", "blocat"],
    "depus": ["aprobat", "respins"],
    "aprobat": ["in_implementare"],
    "respins": ["arhivat", "draft"],
    "in_implementare": ["suspendat", "finalizat"],
    "suspendat": ["in_implementare", "arhivat"],
    "finalizat": ["audit_post", "arhivat"],
    "audit_post": ["arhivat"],
    "arhivat": []
}

STATE_LABELS = {
    "draft": "Ciornă",
    "pre_eligibil": "Pre-eligibil verificat",
    "blocat": "Blocat",
    "conform": "Conform - Pregătit depunere",
    "depus": "Depus",
    "aprobat": "Aprobat",
    "respins": "Respins",
    "in_implementare": "În implementare",
    "suspendat": "Suspendat",
    "finalizat": "Finalizat",
    "audit_post": "Audit post-implementare",
    "arhivat": "Arhivat"
}

class CreateProjectRequest(BaseModel):
    titlu: str
    organizatie_id: str
    program_finantare: str
    descriere: Optional[str] = None
    buget_estimat: Optional[float] = 0
    obiective: Optional[List[str]] = []

class TransitionRequest(BaseModel):
    new_state: str
    motiv: Optional[str] = None

class AddMilestoneRequest(BaseModel):
    titlu: str
    descriere: Optional[str] = None
    deadline: str
    buget_alocat: Optional[float] = 0

class AddExpenseRequest(BaseModel):
    descriere: str
    suma: float
    categorie: str
    milestone_id: Optional[str] = None

@router.post("")
async def create_project(req: CreateProjectRequest, current_user: dict = Depends(get_current_user)):
    await require_org_permission(current_user["user_id"], req.organizatie_id, "create_project")
    org = await db.organizations.find_one({"id": req.organizatie_id}, {"_id": 0})
    if not org:
        raise HTTPException(status_code=404, detail="Organizație negăsită")
    project_id = str(uuid.uuid4())
    project = {
        "id": project_id,
        "titlu": req.titlu,
        "organizatie_id": req.organizatie_id,
        "organizatie_denumire": org["denumire"],
        "program_finantare": req.program_finantare,
        "descriere": req.descriere or "",
        "buget_estimat": req.buget_estimat,
        "buget_aprobat": 0,
        "cheltuieli_totale": 0,
        "obiective": req.obiective,
        "stare": "draft",
        "stare_label": STATE_LABELS["draft"],
        "history": [{
            "from_state": None,
            "to_state": "draft",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": current_user["user_id"],
            "motiv": "Proiect creat"
        }],
        "milestones": [],
        "expenses": [],
        "eligibility_score": None,
        "compliance_report": None,
        "members": [{"user_id": current_user["user_id"], "rol": "owner"}],
        "blocaje": [],
        "documents": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "created_by": current_user["user_id"]
    }
    await db.projects.insert_one(project)
    await db.audit_log.insert_one({
        "id": str(uuid.uuid4()),
        "action": "project.created",
        "entity_type": "project",
        "entity_id": project_id,
        "user_id": current_user["user_id"],
        "details": {"titlu": req.titlu, "program": req.program_finantare},
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    project.pop("_id", None)
    return project

@router.get("")
async def list_projects(organizatie_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    query = {"members.user_id": current_user["user_id"]}
    if organizatie_id:
        query["organizatie_id"] = organizatie_id
    projects = await db.projects.find(query, {"_id": 0}).to_list(100)
    return projects

@router.get("/states")
async def get_states():
    return {"states": STATE_LABELS, "transitions": VALID_TRANSITIONS}

@router.get("/{project_id}")
async def get_project(project_id: str, current_user: dict = Depends(get_current_user)):
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Proiect negăsit")
    return project

@router.post("/{project_id}/transition")
async def transition_project(project_id: str, req: TransitionRequest, current_user: dict = Depends(get_current_user)):
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Proiect negăsit")
    current_state = project["stare"]
    if req.new_state not in VALID_TRANSITIONS.get(current_state, []):
        raise HTTPException(status_code=400, detail=f"Tranziția de la '{current_state}' la '{req.new_state}' nu este permisă")
    transition_entry = {
        "from_state": current_state,
        "to_state": req.new_state,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": current_user["user_id"],
        "motiv": req.motiv or ""
    }
    await db.projects.update_one({"id": project_id}, {
        "$set": {
            "stare": req.new_state,
            "stare_label": STATE_LABELS.get(req.new_state, req.new_state),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        "$push": {"history": transition_entry}
    })
    await db.audit_log.insert_one({
        "id": str(uuid.uuid4()),
        "action": "project.transition",
        "entity_type": "project",
        "entity_id": project_id,
        "user_id": current_user["user_id"],
        "details": {"from": current_state, "to": req.new_state, "motiv": req.motiv},
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    return {"message": f"Proiect mutat în starea '{STATE_LABELS.get(req.new_state)}'", "new_state": req.new_state}

@router.post("/{project_id}/milestones")
async def add_milestone(project_id: str, req: AddMilestoneRequest, current_user: dict = Depends(get_current_user)):
    milestone = {
        "id": str(uuid.uuid4()),
        "titlu": req.titlu,
        "descriere": req.descriere or "",
        "deadline": req.deadline,
        "buget_alocat": req.buget_alocat,
        "cheltuieli": 0,
        "status": "planificat",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.projects.update_one({"id": project_id}, {"$push": {"milestones": milestone}})
    return milestone

@router.post("/{project_id}/expenses")
async def add_expense(project_id: str, req: AddExpenseRequest, current_user: dict = Depends(get_current_user)):
    expense = {
        "id": str(uuid.uuid4()),
        "descriere": req.descriere,
        "suma": req.suma,
        "categorie": req.categorie,
        "milestone_id": req.milestone_id,
        "status": "inregistrata",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": current_user["user_id"]
    }
    await db.projects.update_one({"id": project_id}, {
        "$push": {"expenses": expense},
        "$inc": {"cheltuieli_totale": req.suma}
    })
    return expense

@router.put("/{project_id}")
async def update_project(project_id: str, updates: dict, current_user: dict = Depends(get_current_user)):
    allowed_fields = ["titlu", "descriere", "buget_estimat", "obiective", "program_finantare"]
    update_data = {k: v for k, v in updates.items() if k in allowed_fields}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.projects.update_one({"id": project_id}, {"$set": update_data})
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    return project
