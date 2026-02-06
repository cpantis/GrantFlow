from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from datetime import datetime, timezone
from middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/api/admin", tags=["admin"])
db = None

def set_db(database):
    global db
    db = database

@router.get("/audit-log")
async def get_audit_log(
    entity_type: Optional[str] = None,
    user_id: Optional[str] = None,
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    user = await db.users.find_one({"id": current_user["user_id"]}, {"_id": 0})
    if not user or not user.get("is_admin", False):
        # Allow non-admins to see their own audit log
        query = {"user_id": current_user["user_id"]}
    else:
        query = {}
    if entity_type:
        query["entity_type"] = entity_type
    if user_id and user.get("is_admin"):
        query["user_id"] = user_id
    logs = await db.audit_log.find(query, {"_id": 0}).sort("timestamp", -1).to_list(limit)
    return logs

@router.get("/users")
async def list_users(current_user: dict = Depends(get_current_user)):
    user = await db.users.find_one({"id": current_user["user_id"]}, {"_id": 0})
    if not user or not user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Acces interzis")
    users = await db.users.find({}, {"_id": 0, "password_hash": 0}).to_list(200)
    return users

@router.put("/users/{user_id}/toggle-active")
async def toggle_user_active(user_id: str, current_user: dict = Depends(get_current_user)):
    admin = await db.users.find_one({"id": current_user["user_id"]}, {"_id": 0})
    if not admin or not admin.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Acces interzis")
    target = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="Utilizator negăsit")
    new_status = not target.get("is_active", True)
    await db.users.update_one({"id": user_id}, {"$set": {"is_active": new_status}})
    return {"message": f"Utilizator {'activat' if new_status else 'dezactivat'}", "is_active": new_status}

@router.get("/dashboard")
async def admin_dashboard(current_user: dict = Depends(get_current_user)):
    total_users = await db.users.count_documents({})
    total_orgs = await db.organizations.count_documents({})
    total_projects = await db.projects.count_documents({})
    total_docs = await db.documents.count_documents({})
    total_specialists = await db.specialists.count_documents({})
    projects_by_state = {}
    async for p in db.projects.find({}, {"stare": 1, "_id": 0}):
        state = p.get("stare", "unknown")
        projects_by_state[state] = projects_by_state.get(state, 0) + 1
    recent_audit = await db.audit_log.find({}, {"_id": 0}).sort("timestamp", -1).to_list(10)
    return {
        "stats": {
            "total_users": total_users,
            "total_organizations": total_orgs,
            "total_projects": total_projects,
            "total_documents": total_docs,
            "total_specialists": total_specialists
        },
        "projects_by_state": projects_by_state,
        "recent_audit": recent_audit
    }
