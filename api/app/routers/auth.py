from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.db import get_db
from app.core.security import hash_password, verify_password
from app.core.jwt import create_access_token
from app.schemas.auth import RegisterIn, LoginIn, TokenOut
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=TokenOut)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    email = payload.email.lower()
    existing = db.scalar(select(User).where(User.email == email))
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    u = User(
        full_name=payload.full_name,
        email=email,
        password_hash=hash_password(payload.password),
        is_active=True,
    )
    db.add(u)
    db.commit()
    db.refresh(u)

    token = create_access_token(subject=str(u.id))
    return TokenOut(access_token=token)

@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    email = payload.email.lower()
    u = db.scalar(select(User).where(User.email == email))
    if not u or not verify_password(payload.password, u.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not u.is_active:
        raise HTTPException(status_code=403, detail="Inactive user")

    token = create_access_token(subject=str(u.id))
    return TokenOut(access_token=token)
