"""RBAC Middleware - Role-Based Access Control enforcement"""
from fastapi import Request, HTTPException
from services.auth_service import decode_token
from typing import Optional, List

async def get_current_user(request: Request) -> dict:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token lipsă sau invalid")
    token = auth_header.split(" ")[1]
    try:
        payload = decode_token(token)
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Token expirat sau invalid")


# DB reference - set from server.py
_db = None

def set_rbac_db(database):
    global _db
    _db = database


async def _get_user_org_role(user_id: str, org_id: str) -> Optional[dict]:
    """Get user's role and authorization within an organization."""
    org = await _db.organizations.find_one({"id": org_id}, {"_id": 0})
    if not org:
        return None
    member = next((m for m in org.get("members", []) if m["user_id"] == user_id), None)
    if not member:
        return None

    role = member.get("rol", "viewer")
    active_auth = None

    # For imputernicit, check active authorization
    if role == "imputernicit":
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()
        for auth in org.get("authorizations", []):
            if (auth.get("user_id") == user_id
                and auth.get("status") == "activa"
                and auth.get("valabil_pana", "") >= now[:10]):
                active_auth = auth
                break
        if not active_auth:
            # Authorization expired or revoked
            return {"role": "imputernicit", "active": False, "scope": [], "org_id": org_id}

    return {
        "role": role,
        "active": True,
        "scope": active_auth.get("scope", []) if active_auth else [],
        "org_id": org_id
    }


async def _get_user_project_role(user_id: str, project_id: str) -> Optional[dict]:
    """Get user's role within a project."""
    project = await _db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        return None
    member = next((m for m in project.get("members", []) if m["user_id"] == user_id), None)
    if not member:
        # Fallback: check via organization membership
        org_role = await _get_user_org_role(user_id, project.get("organizatie_id", ""))
        if org_role and org_role.get("active"):
            return {"role": org_role["role"], "project_id": project_id, "org_id": project.get("organizatie_id")}
        return None
    return {"role": member.get("rol", "viewer"), "project_id": project_id, "org_id": project.get("organizatie_id")}


# Permission definitions per role
ROLE_PERMISSIONS = {
    "owner": {
        "org": ["read", "write", "delete", "manage_members", "manage_authorizations", "create_project", "export", "audit"],
        "project": ["read", "write", "delete", "transition", "manage_members", "upload_doc", "compliance", "export"],
        "document": ["read", "write", "delete", "upload", "version", "change_status"],
    },
    "imputernicit": {
        "org": ["read"],
        "project": ["read", "write", "upload_doc", "compliance"],
        "document": ["read", "write", "upload", "version"],
    },
    "consultant": {
        "org": ["read_limited"],
        "project": ["read", "upload_doc", "compliance"],
        "document": ["read", "upload"],
    },
}


def has_permission(role: str, context: str, permission: str) -> bool:
    """Check if a role has a specific permission in a context."""
    perms = ROLE_PERMISSIONS.get(role, {}).get(context, [])
    return permission in perms


async def require_org_permission(user_id: str, org_id: str, permission: str):
    """Raise 403 if user lacks the required organization permission."""
    role_info = await _get_user_org_role(user_id, org_id)
    if not role_info:
        raise HTTPException(status_code=403, detail="Nu aveți acces la această organizație")
    if not role_info.get("active", False):
        raise HTTPException(status_code=403, detail="Împuternicirea a expirat sau a fost revocată")
    if not has_permission(role_info["role"], "org", permission):
        raise HTTPException(status_code=403, detail=f"Nu aveți permisiunea '{permission}' pentru această organizație")
    return role_info


async def require_project_permission(user_id: str, project_id: str, permission: str):
    """Raise 403 if user lacks the required project permission."""
    role_info = await _get_user_project_role(user_id, project_id)
    if not role_info:
        raise HTTPException(status_code=403, detail="Nu aveți acces la acest proiect")
    if not has_permission(role_info["role"], "project", permission):
        raise HTTPException(status_code=403, detail=f"Nu aveți permisiunea '{permission}' pentru acest proiect")
    return role_info


async def require_doc_permission(user_id: str, doc_id: str, permission: str):
    """Raise 403 if user lacks the required document permission."""
    doc = await _db.documents.find_one({"id": doc_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Document negăsit")
    # Check via organization
    org_role = await _get_user_org_role(user_id, doc.get("organizatie_id", ""))
    if org_role and org_role.get("active") and has_permission(org_role["role"], "document", permission):
        return org_role
    # Check via project
    if doc.get("project_id"):
        proj_role = await _get_user_project_role(user_id, doc["project_id"])
        if proj_role and has_permission(proj_role["role"], "document", permission):
            return proj_role
    raise HTTPException(status_code=403, detail=f"Nu aveți permisiunea '{permission}' pentru acest document")
