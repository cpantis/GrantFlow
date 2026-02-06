import os
import jwt
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_token(user_id: str, email: str) -> str:
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=int(os.environ.get("JWT_EXPIRATION_HOURS", "24"))),
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(payload, os.environ["JWT_SECRET"], algorithm=os.environ.get("JWT_ALGORITHM", "HS256"))

def decode_token(token: str) -> dict:
    return jwt.decode(token, os.environ["JWT_SECRET"], algorithms=[os.environ.get("JWT_ALGORITHM", "HS256")])
