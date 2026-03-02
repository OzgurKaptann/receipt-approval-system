from fastapi import HTTPException
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    # bcrypt limit: 72 bytes
    if password is None:
        raise HTTPException(status_code=400, detail="Password is required")

    pw_bytes = password.encode("utf-8")
    if len(pw_bytes) > 72:
        raise HTTPException(status_code=400, detail="Password too long (max 72 bytes)")

    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
