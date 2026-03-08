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
    amount_try: Optional[Decimal] = Field(default=None, validation_alias="receipt_amount_try", alias="receipt_amount_try", description="Parsed TRY amount")
    transfer_date: Optional[datetime] = None

    tg_chat_id: Optional[str] = None
    tg_message_id: Optional[str] = None

    created_at: datetime

    class Config:
        from_attributes = True

class DashboardMetricsOut(BaseModel):
    total_uploaded: int = 0
    total_approved: int = 0
    total_failed: int = 0
    
    total_try_volume: Decimal = Decimal("0.0")
    total_usd_volume: Decimal = Decimal("0.0")
    
    success_rate: float = 0.0

class DailyInvestmentOut(BaseModel):
    date: str
    amount_try: Decimal
    amount_usd: Decimal
    count: int

class DocumentListOut(BaseModel):
    items: list[DocumentUploadOut]
    total: int

class DocumentDetailOut(DocumentUploadOut):
    ocr_raw_data: Optional[dict] = None
    description: Optional[str] = None
    
    slack_channel_id: Optional[str] = None
    slack_message_ts: Optional[str] = None
    slack_decided_by: Optional[str] = None
    slack_decided_at: Optional[datetime] = None