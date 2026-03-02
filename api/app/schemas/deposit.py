from pydantic import BaseModel
from uuid import UUID
from decimal import Decimal
from datetime import datetime
from typing import Optional

from app.models.enums import DepositStatus


class DepositCreate(BaseModel):
    document_id: UUID
    amount: Decimal


class DepositOut(BaseModel):
    id: UUID
    document_id: UUID
    amount: Decimal
    status: DepositStatus
    created_at: datetime

    class Config:
        from_attributes = True
