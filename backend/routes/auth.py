from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
import uuid
import secrets
from datetime import datetime, timezone, timedelta
from services.auth_service import hash_password, verify_password, create_token
from middleware.auth_middleware import get_current_user
from services.email_service import send_verification_email, send_password_reset_email
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])
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

class ResetPasswordConfirm(BaseModel):
    token: str
    new_password: str = Field(min_length=6)

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6)

class VerifyEmailRequest(BaseModel):
    token: str

class UpdateProfileRequest(BaseModel):
    nume: Optional[str] = None
    prenume: Optional[str] = None
    telefon: Optional[str] = None
    functie: Optional[str] = None

def _generate_token() -> str:
    return secrets.token_urlsafe(32)

@router.post("/register")
async def register(req: RegisterRequest):
    existing = await db.users.find_one({"email": req.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email deja înregistrat")

    user_id = str(uuid.uuid4())
    verification_token = _generate_token()

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
        "email_verified": False,
        "verification_token": verification_token,
        "verification_token_expires": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user_doc)

    # Send verification email
    email_result = await send_verification_email(req.email, verification_token, req.prenume)
    logger.info(f"Verification email result for {req.email}: {email_result}")

    await db.audit_log.insert_one({
        "id": str(uuid.uuid4()),
        "action": "user.registered",
        "entity_type": "user",
        "entity_id": user_id,
        "user_id": user_id,
        "details": {"email": req.email},
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

    token = create_token(user_id, req.email)
    return {
        "token": token,
        "user": {
            "id": user_id,
            "email": req.email,
            "nume": req.nume,
            "prenume": req.prenume,
            "telefon": req.telefon,
            "functie": req.functie,
            "email_verified": False
        },
        "verification_token": verification_token,
        "message": "Cont creat. Verificați emailul pentru activare."
    }

@router.post("/verify-email")
async def verify_email(req: VerifyEmailRequest):
    user = await db.users.find_one({"verification_token": req.token})
    if not user:
        raise HTTPException(status_code=400, detail="Token de verificare invalid")

    expires = user.get("verification_token_expires", "")
    if expires and expires < datetime.now(timezone.utc).isoformat():
        raise HTTPException(status_code=400, detail="Token de verificare expirat")

    await db.users.update_one({"id": user["id"]}, {
        "$set": {
            "email_verified": True,
            "verification_token": None,
            "verification_token_expires": None,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    })

    await db.audit_log.insert_one({
        "id": str(uuid.uuid4()),
        "action": "user.email_verified",
        "entity_type": "user",
        "entity_id": user["id"],
        "user_id": user["id"],
        "details": {"email": user["email"]},
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

    return {"message": "Email verificat cu succes"}

@router.post("/resend-verification")
async def resend_verification(current_user: dict = Depends(get_current_user)):
    user = await db.users.find_one({"id": current_user["user_id"]})
    if not user:
        raise HTTPException(status_code=404, detail="Utilizator negăsit")
    if user.get("email_verified"):
        raise HTTPException(status_code=400, detail="Emailul este deja verificat")

    new_token = _generate_token()
    await db.users.update_one({"id": user["id"]}, {
        "$set": {
            "verification_token": new_token,
            "verification_token_expires": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    })

    logger.info(f"[EMAIL MOCK] New verification token for {user['email']}: {new_token}")
    return {"message": "Token de verificare retrimis", "verification_token": new_token}

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
            "is_admin": user.get("is_admin", False),
            "email_verified": user.get("email_verified", False)
        }
    }

@router.post("/reset-password")
async def request_reset_password(req: ResetPasswordRequest):
    user = await db.users.find_one({"email": req.email})
    if not user:
        # Don't reveal if email exists
        return {"message": "Dacă adresa de email există, veți primi un link de resetare."}

    reset_token = _generate_token()
    await db.users.update_one({"id": user["id"]}, {
        "$set": {
            "reset_token": reset_token,
            "reset_token_expires": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
            "reset_token_used": False,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    })

    # Rate limiting check
    recent_resets = await db.audit_log.count_documents({
        "action": "user.password_reset_requested",
        "details.email": req.email,
        "timestamp": {"$gte": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()}
    })
    if recent_resets >= 3:
        raise HTTPException(status_code=429, detail="Prea multe cereri de resetare. Încercați mai târziu.")

    await db.audit_log.insert_one({
        "id": str(uuid.uuid4()),
        "action": "user.password_reset_requested",
        "entity_type": "user",
        "entity_id": user["id"],
        "user_id": user["id"],
        "details": {"email": req.email},
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

    logger.info(f"[EMAIL MOCK] Password reset token for {req.email}: {reset_token}")
    return {"message": "Dacă adresa de email există, veți primi un link de resetare.", "reset_token": reset_token}

@router.post("/reset-password/confirm")
async def confirm_reset_password(req: ResetPasswordConfirm):
    user = await db.users.find_one({"reset_token": req.token, "reset_token_used": False})
    if not user:
        raise HTTPException(status_code=400, detail="Token de resetare invalid sau deja folosit")

    expires = user.get("reset_token_expires", "")
    if expires and expires < datetime.now(timezone.utc).isoformat():
        raise HTTPException(status_code=400, detail="Token de resetare expirat")

    await db.users.update_one({"id": user["id"]}, {
        "$set": {
            "password_hash": hash_password(req.new_password),
            "reset_token": None,
            "reset_token_expires": None,
            "reset_token_used": True,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    })

    await db.audit_log.insert_one({
        "id": str(uuid.uuid4()),
        "action": "user.password_reset_completed",
        "entity_type": "user",
        "entity_id": user["id"],
        "user_id": user["id"],
        "details": {"email": user["email"]},
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

    return {"message": "Parola a fost resetată cu succes"}

@router.post("/change-password")
async def change_password(req: ChangePasswordRequest, current_user: dict = Depends(get_current_user)):
    user = await db.users.find_one({"id": current_user["user_id"]})
    if not user:
        raise HTTPException(status_code=404, detail="Utilizator negăsit")
    if not verify_password(req.current_password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Parola curentă este incorectă")

    await db.users.update_one({"id": user["id"]}, {
        "$set": {
            "password_hash": hash_password(req.new_password),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    })

    await db.audit_log.insert_one({
        "id": str(uuid.uuid4()),
        "action": "user.password_changed",
        "entity_type": "user",
        "entity_id": user["id"],
        "user_id": user["id"],
        "details": {},
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

    return {"message": "Parola a fost schimbată cu succes"}

@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    user = await db.users.find_one({"id": current_user["user_id"]}, {"_id": 0, "password_hash": 0, "verification_token": 0, "reset_token": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Utilizator negăsit")
    return user

@router.put("/profile")
async def update_profile(req: UpdateProfileRequest, current_user: dict = Depends(get_current_user)):
    update_data = {k: v for k, v in req.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.users.update_one({"id": current_user["user_id"]}, {"$set": update_data})
    user = await db.users.find_one({"id": current_user["user_id"]}, {"_id": 0, "password_hash": 0, "verification_token": 0, "reset_token": 0})
    return user
