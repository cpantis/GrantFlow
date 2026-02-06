from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from typing import Optional, List
import uuid
import os
from datetime import datetime, timezone
from middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/api/documents", tags=["documents"])
db = None
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")

def set_db(database):
    global db
    db = database

DOCUMENT_TYPES = [
    "cerere_finantare", "memoriu", "declaratie", "contract", "factura",
    "dovada_plata", "proces_verbal", "ci", "bilant", "balanta",
    "autorizatie", "certificat", "oferta", "cv", "imputernicire", "altele"
]

DOCUMENT_PHASES = ["achizitii", "depunere", "contractare", "implementare", "clarificari"]
DOCUMENT_STATUSES = ["draft", "de_semnat", "semnat", "depus", "aprobat"]

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    organizatie_id: str = Form(...),
    project_id: Optional[str] = Form(None),
    tip: str = Form("altele"),
    faza: Optional[str] = Form(None),
    descriere: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user)
):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    doc_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1] if file.filename else ""
    safe_name = f"{doc_id}{ext}"
    file_path = os.path.join(UPLOAD_DIR, safe_name)
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    doc = {
        "id": doc_id,
        "filename": file.filename,
        "stored_name": safe_name,
        "file_size": len(content),
        "content_type": file.content_type,
        "organizatie_id": organizatie_id,
        "project_id": project_id,
        "tip": tip,
        "faza": faza,
        "status": "draft",
        "descriere": descriere or "",
        "versiune": 1,
        "versions": [{
            "versiune": 1,
            "filename": file.filename,
            "stored_name": safe_name,
            "file_size": len(content),
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
            "uploaded_by": current_user["user_id"]
        }],
        "ocr_status": "pending",
        "ocr_data": None,
        "tags": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "created_by": current_user["user_id"]
    }
    await db.documents.insert_one(doc)
    await db.audit_log.insert_one({
        "id": str(uuid.uuid4()),
        "action": "document.uploaded",
        "entity_type": "document",
        "entity_id": doc_id,
        "user_id": current_user["user_id"],
        "details": {"filename": file.filename, "tip": tip},
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    doc.pop("_id", None)
    return doc

@router.get("")
async def list_documents(
    organizatie_id: Optional[str] = None,
    project_id: Optional[str] = None,
    tip: Optional[str] = None,
    faza: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {}
    if organizatie_id:
        query["organizatie_id"] = organizatie_id
    if project_id:
        query["project_id"] = project_id
    if tip:
        query["tip"] = tip
    if faza:
        query["faza"] = faza
    docs = await db.documents.find(query, {"_id": 0}).to_list(200)
    return docs

@router.get("/types")
async def get_document_types():
    return {"types": DOCUMENT_TYPES, "phases": DOCUMENT_PHASES, "statuses": DOCUMENT_STATUSES}

@router.get("/{doc_id}")
async def get_document(doc_id: str, current_user: dict = Depends(get_current_user)):
    doc = await db.documents.find_one({"id": doc_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Document negăsit")
    return doc

@router.post("/{doc_id}/version")
async def upload_new_version(
    doc_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    doc = await db.documents.find_one({"id": doc_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Document negăsit")
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    new_version = doc["versiune"] + 1
    ext = os.path.splitext(file.filename)[1] if file.filename else ""
    safe_name = f"{doc_id}_v{new_version}{ext}"
    file_path = os.path.join(UPLOAD_DIR, safe_name)
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    version_entry = {
        "versiune": new_version,
        "filename": file.filename,
        "stored_name": safe_name,
        "file_size": len(content),
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "uploaded_by": current_user["user_id"]
    }
    await db.documents.update_one({"id": doc_id}, {
        "$set": {
            "versiune": new_version,
            "filename": file.filename,
            "stored_name": safe_name,
            "file_size": len(content),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        "$push": {"versions": version_entry}
    })
    return {"message": f"Versiunea {new_version} încărcată", "version": version_entry}

@router.put("/{doc_id}/status")
async def update_document_status(doc_id: str, status: str, current_user: dict = Depends(get_current_user)):
    if status not in DOCUMENT_STATUSES:
        raise HTTPException(status_code=400, detail="Status invalid")
    await db.documents.update_one({"id": doc_id}, {"$set": {"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}})
    return {"message": f"Status actualizat: {status}"}
