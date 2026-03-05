import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import String, DateTime, func, ForeignKey, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Deposit(Base):
    __tablename__ = "deposits"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("uploaded_documents.id"), unique=True, nullable=False
    )

    mt_account_id: Mapped[str] = mapped_column(String(80), nullable=False)

    # Original FX fields (kept for compatibility)
    src_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    src_currency: Mapped[str] = mapped_column(String(3), nullable=False)

    fx_rate: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    dst_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    dst_currency: Mapped[str] = mapped_column(String(3), nullable=False)

    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    provider_ref: Mapped[str | None] = mapped_column(String(120), nullable=True)

    # Sprint-2 convenience fields
    amount_try: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    amount_usd: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)

    status: Mapped[str] = mapped_column(String(32), nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
