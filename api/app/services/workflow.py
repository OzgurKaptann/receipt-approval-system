from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Literal, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.document import UploadedDocument
from app.models.deposit import Deposit
from app.models.customer import Customer
from app.models.enums import DocumentStatus, DepositStatus
from app.services.audit import write_audit_event
from app.services import slack as slack_service


def on_telegram_approved(document_id: UUID, db: Session) -> None:
    """
    Telegram approval side-effect: transition to SLACK_PENDING and send Slack message.

    Idempotent with respect to Slack sending: if the document is already in a
    Slack terminal state (SLACK_PENDING/SLACK_APPROVED/SLACK_REJECTED), this
    function becomes a no-op.
    """
    doc = db.query(UploadedDocument).filter(UploadedDocument.id == document_id).with_for_update(of=UploadedDocument).first()
    if not doc:
        return

    if doc.status in (
        DocumentStatus.SLACK_PENDING.value,
        DocumentStatus.SLACK_APPROVED.value,
        DocumentStatus.SLACK_REJECTED.value,
    ):
        return

    doc.status = DocumentStatus.SLACK_PENDING.value
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Use Celery task to send Slack notification instead of synchronous call
    from app.worker import send_slack_approval_task
    send_slack_approval_task.delay(str(doc.id))


def on_slack_action(
    db: Session,
    *,
    public_key: str,
    action: Literal["approve", "reject"],
    actor: dict[str, Any],
) -> Tuple[UploadedDocument, Optional[Deposit]]:
    """
    Handle Slack interactive approval/rejection and dispatch the finalize worker.
    """
    doc = (
        db.query(UploadedDocument)
        .filter(UploadedDocument.public_key == public_key)
        .with_for_update(of=UploadedDocument)
        .first()
    )
    if not doc:
        raise ValueError("Document not found")

    actor_id = actor.get("username") or actor.get("id") or "unknown"
    existing_dep = db.query(Deposit).filter(Deposit.document_id == doc.id).first()

    if action == "approve":
        if doc.status in (DocumentStatus.SLACK_APPROVED.value, DocumentStatus.APPROVED.value):
            return doc, existing_dep

        doc.status = DocumentStatus.SLACK_APPROVED.value
        db.add(doc)
        db.commit()
        db.refresh(doc)

        write_audit_event(
            db,
            document_id=doc.id,
            event_type="SLACK_APPROVED",
            actor_type="SLACK",
            actor_id=actor_id,
            payload={},
        )

        from app.worker import finalize_and_deposit_task
        finalize_and_deposit_task.delay(str(doc.id), True)

        return doc, existing_dep

    if action == "reject":
        if doc.status in (DocumentStatus.SLACK_REJECTED.value, DocumentStatus.REJECTED.value):
            return doc, existing_dep

        doc.status = DocumentStatus.SLACK_REJECTED.value
        db.add(doc)
        db.commit()
        db.refresh(doc)

        write_audit_event(
            db,
            document_id=doc.id,
            event_type="SLACK_REJECTED",
            actor_type="SLACK",
            actor_id=actor_id,
            payload={},
        )
        
        from app.worker import finalize_and_deposit_task
        finalize_and_deposit_task.delay(str(doc.id), False)

        return doc, existing_dep

    raise ValueError(f"Unknown action: {action!r}")


def on_manual_action(
    db: Session,
    *,
    document_id: UUID,
    action: Literal["approve", "reject"],
    actor_id: str,
) -> Tuple[UploadedDocument, Optional[Deposit]]:
    """
    Handle direct UI manual approval/rejection bypassing external bots.
    """
    doc = (
        db.query(UploadedDocument)
        .filter(UploadedDocument.id == document_id)
        .with_for_update(of=UploadedDocument)
        .first()
    )
    if not doc:
        raise ValueError("Document not found")

    existing_dep = db.query(Deposit).filter(Deposit.document_id == doc.id).first()

    if action == "approve":
        if doc.status in (DocumentStatus.SLACK_APPROVED.value, DocumentStatus.APPROVED.value):
            return doc, existing_dep

        doc.status = DocumentStatus.SLACK_APPROVED.value
        db.add(doc)
        db.commit()
        db.refresh(doc)

        write_audit_event(
            db,
            document_id=doc.id,
            event_type="MANUAL_APPROVED",
            actor_type="ADMIN_UI",
            actor_id=actor_id,
            payload={"action": "forced_approve"},
        )

        from app.worker import finalize_and_deposit_task
        finalize_and_deposit_task.delay(str(doc.id), True)

        return doc, existing_dep

    if action == "reject":
        if doc.status in (DocumentStatus.SLACK_REJECTED.value, DocumentStatus.REJECTED.value):
            return doc, existing_dep

        doc.status = DocumentStatus.SLACK_REJECTED.value
        db.add(doc)
        db.commit()
        db.refresh(doc)

        write_audit_event(
            db,
            document_id=doc.id,
            event_type="MANUAL_REJECTED",
            actor_type="ADMIN_UI",
            actor_id=actor_id,
            payload={"action": "forced_reject"},
        )
        
        from app.worker import finalize_and_deposit_task
        finalize_and_deposit_task.delay(str(doc.id), False)

        return doc, existing_dep

    raise ValueError(f"Unknown action: {action!r}")

