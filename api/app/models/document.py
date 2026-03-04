import uuid
from decimal import Decimal
from datetime import datetime

from sqlalchemy import String, DateTime, func, ForeignKey, Numeric, BigInteger, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class UploadedDocument(Base):
    __tablename__ = "uploaded_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)

    # OCR sonrası yazacağız => nullable olmalı
    receipt_amount_try: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)

    # OCR alanları (Sprint-1)
    sender_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    transfer_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    original_file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(120), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    file_sha256: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)

    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(String(32), nullable=False)

    public_key: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)

    tg_chat_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    tg_message_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    tg_decided_by: Mapped[str | None] = mapped_column(String(120), nullable=True)
    tg_decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    slack_channel_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    slack_message_ts: Mapped[str | None] = mapped_column(String(40), nullable=True)
    slack_decided_by: Mapped[str | None] = mapped_column(String(120), nullable=True)
    slack_decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )