from fastapi import Request, HTTPException
from services.auth_service import decode_token

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
