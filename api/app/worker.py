import os
from celery import Celery
from uuid import UUID
from decimal import Decimal

from app.core.settings import settings
from app.core.db import SessionLocal
from app.models.document import UploadedDocument
from app.models.enums import DocumentStatus
from app.services.ocr import parse_receipt
from app.services.telegram import send_approval_message
from app.services.slack import send_approval_request
from app.services.audit import write_audit_event
from app.services.fx import convert_try_to_usd
from app.services.metatrader import execute_deposit
from app.services.crm_callback import notify_crm
from app.models.customer import Customer
from app.models.deposit import Deposit
from app.models.enums import DepositStatus

celery_app = Celery(
    "receipt_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

@celery_app.task(name="process_document_ocr_task", bind=True, max_retries=3)
def process_document_ocr_task(self, document_id: str):
    db = SessionLocal()
    try:
        doc = db.query(UploadedDocument).filter(UploadedDocument.id == document_id).with_for_update().first()
        if not doc:
            return

        if doc.status != DocumentStatus.UPLOADED.value:
            return

        ocr = parse_receipt(file_path=doc.file_path, original_file_name=doc.original_file_name)

        doc.sender_name = ocr.sender_name
        doc.receipt_amount_try = ocr.amount_try
        doc.transfer_date = ocr.transfer_date
        doc.ocr_raw_data = ocr.raw_response
        doc.status = DocumentStatus.TG_PENDING.value
        db.add(doc)
        db.commit()
        db.refresh(doc)

        write_audit_event(
            db,
            document_id=doc.id,
            event_type="OCR_PARSED",
            actor_type="SYSTEM",
            actor_id=ocr.provider,
            payload={
                "sender_name": doc.sender_name,
                "amount_try": str(doc.receipt_amount_try) if doc.receipt_amount_try is not None else None,
                "transfer_date": doc.transfer_date.isoformat() if doc.transfer_date else None,
            },
        )
        
        # Chain next task
        send_telegram_approval_task.delay(str(doc.id))

    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc, countdown=5)
    finally:
        db.close()

@celery_app.task(name="send_telegram_approval_task", bind=True, max_retries=3)
def send_telegram_approval_task(self, document_id: str):
    db = SessionLocal()
    try:
        doc = db.query(UploadedDocument).filter(UploadedDocument.id == document_id).with_for_update().first()
        if not doc or doc.status != DocumentStatus.TG_PENDING.value:
            return

        msg_text = (
            "🧾 *Receipt Approval*\n"
            f"- public_key: `{doc.public_key}`\n"
            f"- sender: {doc.sender_name}\n"
            f"- amount_try: {doc.receipt_amount_try}\n"
            f"- transfer_date: {doc.transfer_date}\n"
        )

        tg = send_approval_message(public_key=doc.public_key, text=msg_text)

        if tg.ok:
            doc.tg_chat_id = tg.chat_id
            doc.tg_message_id = tg.message_id
            db.add(doc)
            db.commit()
            db.refresh(doc)

            write_audit_event(
                db,
                document_id=doc.id,
                event_type="TG_SENT",
                actor_type="SYSTEM",
                actor_id="telegram",
                payload={"tg_chat_id": tg.chat_id, "tg_message_id": tg.message_id},
            )
        else:
            write_audit_event(
                db,
                document_id=doc.id,
                event_type="TG_SEND_FAILED",
                actor_type="SYSTEM",
                actor_id="telegram",
                payload={"error": tg.error},
            )
            raise Exception(f"Telegram send failed: {tg.error}")

    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc, countdown=10)
    finally:
        db.close()


@celery_app.task(name="send_slack_approval_task", bind=True, max_retries=3)
def send_slack_approval_task(self, document_id: str):
    db = SessionLocal()
    try:
        doc = db.query(UploadedDocument).filter(UploadedDocument.id == document_id).with_for_update().first()
        if not doc or doc.status != DocumentStatus.SLACK_PENDING.value:
            return

        channel_id, message_ts = send_approval_request(
            public_key=doc.public_key,
            sender_name=doc.sender_name,
            amount_try=doc.receipt_amount_try,
            transfer_date=doc.transfer_date,
        )

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
    except Exception as exc:
        db.rollback()
        write_audit_event(
            db,
            document_id=doc.id,  # type: ignore
            event_type="SLACK_SEND_FAILED",
            actor_type="SYSTEM",
            actor_id="slack",
            payload={"error": str(exc)},
        )
        raise self.retry(exc=exc, countdown=10)
    finally:
        db.close()


@celery_app.task(name="finalize_and_deposit_task", bind=True, max_retries=3)
def finalize_and_deposit_task(self, document_id: str, is_approved: bool):
    """
    Executes the final block of the workflow: FX calculation, Metatrader Deposit, CRM Callback.
    """
    db = SessionLocal()
    try:
        # Re-fetch row with locking to prevent split-brain issues
        doc = db.query(UploadedDocument).filter(UploadedDocument.id == document_id).with_for_update().first()
        if not doc:
            return

        final_status = DocumentStatus.APPROVED.value if is_approved else DocumentStatus.REJECTED.value
        
        # We process deposit only if newly approved
        if is_approved and doc.status != DocumentStatus.APPROVED.value:
            if not doc.receipt_amount_try:
                raise ValueError("Cannot deposit without valid amount")
                
            customer = db.query(Customer).filter(Customer.id == doc.customer_id).first()
            if not customer:
                raise ValueError(f"Customer {doc.customer_id} not found")

            # 1. FX Conversion (TRY -> USD)
            rate = convert_try_to_usd(Decimal("1.0"))  # Get the raw rate via the 1 unit abstraction or we can just fetch get_usd_try_rate
            from app.services.fx import get_usd_try_rate
            fx_rate = get_usd_try_rate()
            amount_usd = convert_try_to_usd(doc.receipt_amount_try)
            
            # Create Deposit in Pending State if not exists
            dep = db.query(Deposit).filter(Deposit.document_id == doc.id).first()
            if not dep:
                dep = Deposit(
                    document_id=doc.id,
                    mt_account_id=customer.mt_account_id,
                    src_amount=float(doc.receipt_amount_try),
                    src_currency="TRY",
                    fx_rate=float(fx_rate),
                    dst_amount=float(amount_usd),
                    dst_currency="USD",
                    provider="FX_MANUAL",
                    provider_ref=None,
                    status=DepositStatus.DEPOSIT_PENDING.value,
                    error_message=None,
                    amount_try=doc.receipt_amount_try,
                    amount_usd=amount_usd,
                )
                db.add(dep)
                db.commit()
                db.refresh(dep)
            
            # 2. MT Deposit
            mt_result = execute_deposit(
                mt_account_id=customer.mt_account_id,
                mt_currency=customer.mt_currency,
                amount=amount_usd
            )
            
            if not mt_result.success:
                dep.status = DepositStatus.DEPOSIT_FAILED.value
                dep.error_message = mt_result.error_message
                db.add(dep)
                
                write_audit_event(
                    db,
                    document_id=doc.id,
                    event_type="API_MT_DEPOSIT_FAILED",
                    actor_type="SYSTEM",
                    actor_id="metatrader",
                    payload={"error": mt_result.error_message}
                )
                db.commit()
                raise Exception(f"MT Deposit failed: {mt_result.error_message}")

            # Update Document and Deposit state
            doc.status = DocumentStatus.APPROVED.value
            dep.status = DepositStatus.DEPOSIT_SUCCESS.value
            dep.provider_ref = mt_result.transaction_id
            db.add(doc)
            db.add(dep)
            db.commit()
            
            write_audit_event(
                db,
                document_id=doc.id,
                event_type="API_MT_DEPOSIT_OK",
                actor_type="SYSTEM",
                actor_id="metatrader",
                payload={"mt_tx_id": mt_result.transaction_id, "amount_usd": str(amount_usd)}
            )
            
            # 3. CRM Callback
            notify_crm(
                document_id=doc.id,
                status="APPROVED",
                final_amount_try=doc.receipt_amount_try,
                final_amount_usd=amount_usd,
                mt_transaction_id=mt_result.transaction_id
            )
            
        elif not is_approved and doc.status != DocumentStatus.REJECTED.value:
            # 3. CRM Callback (Reject mode)
            doc.status = DocumentStatus.REJECTED.value
            db.add(doc)
            db.commit()
            
            notify_crm(
                document_id=doc.id,
                status="REJECTED",
                final_amount_try=None,
                final_amount_usd=None
            )

    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc, countdown=15)
    finally:
        db.close()
