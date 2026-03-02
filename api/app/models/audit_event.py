import uuid
from sqlalchemy import String, DateTime, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class AuditEvent(Base):
    __tablename__ = 'audit_events'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey('uploaded_documents.id'), nullable=True)

    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    actor_type: Mapped[str] = mapped_column(String(20), nullable=False)
    actor_id: Mapped[str | None] = mapped_column(String(120), nullable=True)

    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
