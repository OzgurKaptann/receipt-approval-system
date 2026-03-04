from typing import Any, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent


def write_audit_event(
    db: Session,
    *,
    document_id: Optional[UUID],
    event_type: str,
    actor_type: str,
    actor_id: Optional[str],
    payload: dict[str, Any],
) -> None:
    ev = AuditEvent(
        document_id=document_id,
        event_type=event_type,
        actor_type=actor_type,
        actor_id=actor_id,
        payload=payload or {},
    )
    db.add(ev)
    db.commit()