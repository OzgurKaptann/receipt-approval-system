from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentUploadOut(BaseModel):
    id: UUID
    public_key: str
    status: str

    customer_id: UUID

    original_file_name: str
    storage_file_name: str
    file_path: str
    mime_type: str
    file_size: int
    file_sha256: str

    # OCR parsed
    sender_name: Optional[str] = None
    amount_try: Optional[Decimal] = Field(default=None, description="Parsed TRY amount")
    transfer_date: Optional[datetime] = None

    tg_chat_id: Optional[str] = None
    tg_message_id: Optional[str] = None

    created_at: datetime

    class Config:
        from_attributes = True