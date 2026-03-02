# api/app/core/db.py
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ✅ Tek Base kaynağı: modellerin Base'i
from app.models.base import Base

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set (check .env and docker compose env_file)")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()