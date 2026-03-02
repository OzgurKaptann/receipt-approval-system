from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class DocumentCreate(BaseModel):
    customer_id: UUID
    file_name: str
    mime_type: Optional[str] = None
    storage_path: Optional[str] = None


class DocumentOut(BaseModel):
    id: UUID
    customer_id: UUID
    file_name: str
    mime_type: Optional[str] = None
    storage_path: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
