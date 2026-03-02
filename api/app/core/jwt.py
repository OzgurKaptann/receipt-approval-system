from datetime import datetime, timedelta, timezone
from jose import jwt
from app.core.settings import settings

ALGORITHM = "HS256"

def create_access_token(subject: str, expires_minutes: int = 60) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_minutes)).timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])
