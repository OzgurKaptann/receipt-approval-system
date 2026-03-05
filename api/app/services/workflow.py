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
from app.services.fx import get_try_to_usd_rate
from app.services.audit import write_audit_event
from app.services import slack as slack_service


def on_telegram_approved(document_id: UUID, db: Session) -> None:
    """
    Telegram approval side-effect: transition to SLACK_PENDING and send Slack message.

    Idempotent with respect to Slack sending: if the document is already in a
    Slack terminal state (SLACK_PENDING/SLACK_APPROVED/SLACK_REJECTED), this
    function becomes a no-op.
    """
    doc = db.query(UploadedDocument).filter(UploadedDocument.id == document_id).first()
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

    try:
        channel_id, message_ts = slack_service.send_approval_request(
            public_key=doc.public_key,
            sender_name=doc.sender_name,
            amount_try=doc.receipt_amount_try,
            transfer_date=doc.transfer_date,
        )

        # Persist Slack identifiers if columns exist.
        if hasattr(doc, "slack_channel_id"):
            doc.slack_channel_id = channel_id
        if hasattr(doc, "slack_message_ts"):
            doc.slack_message_ts = message_ts

        db.add(doc)
        db.commit()
        db.refresh(doc)

        actor_id = "slack"
        if channel_id == "mock_channel" and message_ts == "mock_ts":
            actor_id = "slack_mock"

        write_audit_event(
            db,
            document_id=doc.id,
            event_type="SLACK_SENT",
            actor_type="SYSTEM",
            actor_id=actor_id,
            payload={
                "slack_channel_id": getattr(doc, "slack_channel_id", None),
                "slack_message_ts": getattr(doc, "slack_message_ts", None),
            },
        )
    except Exception as exc:  # noqa: BLE001
        write_audit_event(
            db,
            document_id=doc.id,
            event_type="SLACK_SEND_FAILED",
            actor_type="SYSTEM",
            actor_id="slack",
            payload={"error": str(exc)},
        )


def on_slack_action(
    db: Session,
    *,
    public_key: str,
    action: Literal["approve", "reject"],
    actor: dict[str, Any],
) -> Tuple[UploadedDocument, Optional[Deposit]]:
    """
    Handle Slack interactive approval/rejection.

    Idempotent:
    - Repeated approve when document is already SLACK_APPROVED returns existing state.
    - Repeated reject when document is already SLACK_REJECTED returns existing state.
    """
    doc = (
        db.query(UploadedDocument)
        .filter(UploadedDocument.public_key == public_key)
        .first()
    )
    if not doc:
        raise ValueError("Document not found")

    actor_id = actor.get("username") or actor.get("id") or "unknown"

    existing_dep = db.query(Deposit).filter(Deposit.document_id == doc.id).first()

    if action == "approve":
        if doc.status == DocumentStatus.SLACK_APPROVED.value:
            return doc, existing_dep

        if doc.receipt_amount_try is None:
            raise ValueError("Document has no receipt_amount_try; cannot create deposit.")

        fx_rate = get_try_to_usd_rate()
        amount_try = Decimal(doc.receipt_amount_try)
        amount_usd = (amount_try * fx_rate).quantize(Decimal("0.01"))

        if existing_dep is None:
            customer = (
                db.query(Customer)
                .filter(Customer.id == doc.customer_id)
                .first()
            )

            mt_account_id = getattr(customer, "mt_account_id", "UNKNOWN")

            dep = Deposit(
                document_id=doc.id,
                mt_account_id=mt_account_id,
                src_amount=float(amount_try),
                src_currency="TRY",
                fx_rate=float(fx_rate),
                dst_amount=float(amount_usd),
                dst_currency="USD",
                provider="FX_MANUAL",
                provider_ref=None,
                status=DepositStatus.DEPOSIT_PENDING.value,
                error_message=None,
                amount_try=amount_try,
                amount_usd=amount_usd,
            )
            db.add(dep)
            db.commit()
            db.refresh(dep)
            existing_dep = dep

            write_audit_event(
                db,
                document_id=doc.id,
                event_type="DEPOSIT_CREATED",
                actor_type="SLACK",
                actor_id=actor_id,
                payload={
                    "deposit_id": str(existing_dep.id),
                    "amount_try": str(amount_try),
                    "amount_usd": str(amount_usd),
                    "fx_rate": str(fx_rate),
                },
            )

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
            payload={"deposit_id": str(existing_dep.id) if existing_dep else None},
        )

        return doc, existing_dep

    if action == "reject":
        if doc.status == DocumentStatus.SLACK_REJECTED.value:
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

        return doc, existing_dep

    raise ValueError(f"Unknown action: {action!r}")

