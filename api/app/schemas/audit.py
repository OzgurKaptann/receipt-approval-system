from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional


class AuditEventOut(BaseModel):
    id: UUID
    actor_user_id: Optional[UUID] = None
    document_id: Optional[UUID] = None
    action: str
    created_at: datetime

    class Config:
        from_attributes = True
