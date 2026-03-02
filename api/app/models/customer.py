import uuid
from sqlalchemy import String, DateTime, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class Customer(Base):
    __tablename__ = 'customers'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)

    crm_customer_id: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    mt_account_id: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    mt_currency: Mapped[str] = mapped_column(String(3), nullable=False)

    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
