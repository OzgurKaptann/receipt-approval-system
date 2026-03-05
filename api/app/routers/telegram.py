from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.audit_event import AuditEvent
from app.models.document import UploadedDocument
from app.models.enums import DocumentStatus
from app.services.workflow import on_telegram_approved


router = APIRouter(prefix="/telegram", tags=["telegram"])


class TgFrom(BaseModel):
    id: Optional[int] = None
    username: Optional[str] = None


class TgCallbackQuery(BaseModel):
    data: Optional[str] = None
    from_: Optional[TgFrom] = None

    class Config:
        fields = {"from_": "from"}


class TgUpdate(BaseModel):
    callback_query: Optional[TgCallbackQuery] = None


@router.post("/webhook")
def telegram_webhook(payload: TgUpdate, db: Session = Depends(get_db)):
    """
    Telegram callback receiver (simülasyon).
    callback_query.data format:
      - approve:<public_key>
      - reject:<public_key>
    """
    cq = payload.callback_query
    if not cq or not cq.data:
        raise HTTPException(status_code=400, detail="Missing callback_query.data")

    raw = cq.data.strip()
    if ":" not in raw:
        raise HTTPException(status_code=400, detail="Invalid callback data format")

    action, public_key = raw.split(":", 1)
    action = action.lower().strip()
    public_key = public_key.strip()

    doc = (
        db.query(UploadedDocument)
        .filter(UploadedDocument.public_key == public_key)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if action == "approve":
        # Do not override Slack terminal states on repeated callbacks.
        if doc.status not in (
            DocumentStatus.SLACK_PENDING.value,
            DocumentStatus.SLACK_APPROVED.value,
            DocumentStatus.SLACK_REJECTED.value,
        ):
            doc.status = DocumentStatus.TG_APPROVED.value
        event_type = "TG_APPROVED"
    elif action == "reject":
        doc.status = DocumentStatus.TG_REJECTED.value
        event_type = "TG_REJECTED"
    else:
        raise HTTPException(status_code=400, detail="Unknown action")

    actor = "unknown"
    if cq.from_:
        # Prefer username, fall back to numeric id when provided.
        if cq.from_.username:
            actor = cq.from_.username
        elif cq.from_.id is not None:
            actor = str(cq.from_.id)

    db.add(
        AuditEvent(
            event_type=event_type,
            actor_type="TELEGRAM",
            actor_id=actor,
            document_id=doc.id,
            created_at=datetime.now(tz=timezone.utc),
        )
    )

    db.commit()

    if action == "approve":
        on_telegram_approved(document_id=doc.id, db=db)
        # Reload the latest status after workflow side-effects (e.g. SLACK_PENDING).
        db.refresh(doc)

    return {"ok": True, "status": doc.status, "public_key": public_key}