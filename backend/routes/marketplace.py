from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
import uuid
from datetime import datetime, timezone
from middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/api/marketplace", tags=["marketplace"])
db = None

def set_db(database):
    global db
    db = database

class CreateSpecialistProfile(BaseModel):
    specializare: str
    descriere: str
    experienta_ani: int
    competente: List[str]
    tarif_orar: Optional[float] = None
    disponibilitate: str = "disponibil"

class AssignSpecialistRequest(BaseModel):
    specialist_id: str
    project_id: str
    rol: str = "consultant"

@router.post("/profile")
async def create_specialist_profile(req: CreateSpecialistProfile, current_user: dict = Depends(get_current_user)):
    existing = await db.specialists.find_one({"user_id": current_user["user_id"]})
    if existing:
        raise HTTPException(status_code=400, detail="Profil deja existent")
    profile_id = str(uuid.uuid4())
    profile = {
        "id": profile_id,
        "user_id": current_user["user_id"],
        "email": current_user["email"],
        "specializare": req.specializare,
        "descriere": req.descriere,
        "experienta_ani": req.experienta_ani,
        "competente": req.competente,
        "tarif_orar": req.tarif_orar,
        "disponibilitate": req.disponibilitate,
        "rating": 0,
        "proiecte_finalizate": 0,
        "is_verified": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.specialists.insert_one(profile)
    profile.pop("_id", None)
    return profile

@router.get("/specialists")
async def list_specialists(
    specializare: Optional[str] = None,
    disponibilitate: Optional[str] = None
):
    query = {}
    if specializare:
        query["specializare"] = {"$regex": specializare, "$options": "i"}
    if disponibilitate:
        query["disponibilitate"] = disponibilitate
    specialists = await db.specialists.find(query, {"_id": 0}).to_list(100)
    # Enrich with user data
    for s in specialists:
        user = await db.users.find_one({"id": s["user_id"]}, {"_id": 0, "password_hash": 0})
        if user:
            s["nume"] = user.get("nume", "")
            s["prenume"] = user.get("prenume", "")
    return specialists

@router.get("/profile/me")
async def get_my_profile(current_user: dict = Depends(get_current_user)):
    profile = await db.specialists.find_one({"user_id": current_user["user_id"]}, {"_id": 0})
    if not profile:
        return None
    return profile

@router.put("/profile")
async def update_specialist_profile(req: CreateSpecialistProfile, current_user: dict = Depends(get_current_user)):
    update_data = req.model_dump()
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.specialists.update_one({"user_id": current_user["user_id"]}, {"$set": update_data})
    profile = await db.specialists.find_one({"user_id": current_user["user_id"]}, {"_id": 0})
    return profile

@router.post("/assign")
async def assign_specialist(req: AssignSpecialistRequest, current_user: dict = Depends(get_current_user)):
    specialist = await db.specialists.find_one({"id": req.specialist_id}, {"_id": 0})
    if not specialist:
        raise HTTPException(status_code=404, detail="Specialist negăsit")
    await db.projects.update_one({"id": req.project_id}, {
        "$push": {"members": {"user_id": specialist["user_id"], "rol": req.rol}}
    })
    return {"message": "Specialist asignat la proiect"}
