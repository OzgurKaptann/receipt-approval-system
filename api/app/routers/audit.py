from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.auth import get_current_user
from app.models.audit_event import AuditEvent
from app.models.user import User
from app.schemas.audit import AuditEventOut

router = APIRouter(prefix="/audit-events", tags=["audit"])


@router.get("", response_model=list[AuditEventOut])
def list_audit_events(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return db.query(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(200).all()
