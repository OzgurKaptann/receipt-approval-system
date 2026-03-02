import uuid
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.db import get_db
from app.core.jwt import decode_token
from app.models.user import User

bearer = HTTPBearer()

def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = decode_token(creds.credentials)
        user_id = uuid.UUID(payload["sub"])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    u = db.scalar(select(User).where(User.id == user_id))
    if not u:
        raise HTTPException(status_code=401, detail="User not found")

    return u
