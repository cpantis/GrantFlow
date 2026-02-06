from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
import uuid
from datetime import datetime, timezone
from services.auth_service import hash_password, verify_password, create_token
from middleware.auth_middleware import get_current_user
from motor.motor_asyncio import AsyncIOMotorClient
import os

router = APIRouter(prefix="/api/auth", tags=["auth"])

# DB reference set in server.py
db = None

def set_db(database):
    global db
    db = database

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    nume: str
    prenume: str
    telefon: Optional[str] = None
    functie: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ResetPasswordRequest(BaseModel):
    email: EmailStr

class UpdateProfileRequest(BaseModel):
    nume: Optional[str] = None
    prenume: Optional[str] = None
    telefon: Optional[str] = None
    functie: Optional[str] = None

@router.post("/register")
async def register(req: RegisterRequest):
    existing = await db.users.find_one({"email": req.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email deja înregistrat")
    user_id = str(uuid.uuid4())
    user_doc = {
        "id": user_id,
        "email": req.email,
        "password_hash": hash_password(req.password),
        "nume": req.nume,
        "prenume": req.prenume,
        "telefon": req.telefon,
        "functie": req.functie,
        "is_active": True,
        "is_admin": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user_doc)
    token = create_token(user_id, req.email)
    return {
        "token": token,
        "user": {
            "id": user_id,
            "email": req.email,
            "nume": req.nume,
            "prenume": req.prenume,
            "telefon": req.telefon,
            "functie": req.functie
        }
    }

@router.post("/login")
async def login(req: LoginRequest):
    user = await db.users.find_one({"email": req.email})
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Email sau parolă incorectă")
    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="Cont dezactivat")
    token = create_token(user["id"], user["email"])
    return {
        "token": token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "nume": user["nume"],
            "prenume": user["prenume"],
            "telefon": user.get("telefon"),
            "functie": user.get("functie"),
            "is_admin": user.get("is_admin", False)
        }
    }

@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    user = await db.users.find_one({"id": current_user["user_id"]}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Utilizator negăsit")
    return user

@router.put("/profile")
async def update_profile(req: UpdateProfileRequest, current_user: dict = Depends(get_current_user)):
    update_data = {k: v for k, v in req.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.users.update_one({"id": current_user["user_id"]}, {"$set": update_data})
    user = await db.users.find_one({"id": current_user["user_id"]}, {"_id": 0, "password_hash": 0})
    return user
