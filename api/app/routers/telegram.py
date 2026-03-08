from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.audit_event import AuditEvent
from app.models.document import UploadedDocument
from app.models.enums import DocumentStatus
from app.services.workflow import on_telegram_approved
from app.core.settings import settings


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


def verify_telegram_secret(x_telegram_bot_api_secret_token: Optional[str] = Header(None)):
    if not settings.TG_WEBHOOK_SECRET:
        return  # Mock/Dev mode bypass if secret not provided
        
    if not x_telegram_bot_api_secret_token or x_telegram_bot_api_secret_token != settings.TG_WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Invalid Telegram secret token")

@router.post("/webhook", dependencies=[Depends(verify_telegram_secret)])
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
        .with_for_update(of=UploadedDocument)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    import logging
    logger = logging.getLogger(__name__)

    if action == "approve":
        if doc.status not in (DocumentStatus.TG_PENDING.value, DocumentStatus.TG_APPROVED.value):
            logger.info(f"Ignoring Telegram approve for {public_key}, current status: {doc.status}")
            return {"ok": True, "status": doc.status, "public_key": public_key, "note": "Already processed"}
            
        doc.status = DocumentStatus.TG_APPROVED.value
        event_type = "TG_APPROVED"
    elif action == "reject":
        if doc.status not in (DocumentStatus.TG_PENDING.value, DocumentStatus.TG_REJECTED.value):
            logger.info(f"Ignoring Telegram reject for {public_key}, current status: {doc.status}")
            return {"ok": True, "status": doc.status, "public_key": public_key, "note": "Already processed"}
            
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

    from app.services.telegram import edit_approval_message

    if action == "approve":
        on_telegram_approved(document_id=doc.id, db=db)
        # Reload the latest status after workflow side-effects (e.g. SLACK_PENDING).
        db.refresh(doc)
        
        new_text = (
            "✅ Dekont onaylandı\n"
            f"- Public Key: `{doc.public_key}`\n"
            f"- Sender: {doc.sender_name}\n"
            f"- Amount: {doc.receipt_amount_try} TRY"
        )
    else:
        new_text = (
            "❌ Dekont reddedildi\n"
            f"- Public Key: `{doc.public_key}`\n"
            f"- Sender: {doc.sender_name}"
        )

    if doc.tg_chat_id and doc.tg_message_id:
        success = edit_approval_message(doc.tg_chat_id, doc.tg_message_id, new_text)
        if success:
            logger.info(f"Telegram message updated to {action.upper()} for {doc.public_key}")
        else:
            logger.warning(f"Failed to update Telegram message for {doc.public_key}")

    return {"ok": True, "status": doc.status, "public_key": public_key}