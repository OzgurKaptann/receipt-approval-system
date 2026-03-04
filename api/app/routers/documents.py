import secrets
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.db import get_db
from app.core.settings import settings
from app.models.document import UploadedDocument
from app.models.enums import DocumentStatus
from app.models.user import User
from app.schemas.document import DocumentUploadOut
from app.services.audit import write_audit_event
from app.services.ocr import parse_receipt_mock
from app.services.storage import save_upload_to_storage
from app.services.telegram import send_approval_message

router = APIRouter(prefix="/documents", tags=["documents"])


def _gen_public_key() -> str:
    # guess edilemeyecek: uuid4 + token_urlsafe
    return f"{secrets.token_hex(16)}_{secrets.token_urlsafe(16)}"


@router.post("/upload", response_model=DocumentUploadOut)
async def upload_document(
    customer_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="file is required")

    ct = (file.content_type or "").lower()
    if ct not in ("image/jpeg", "image/jpg", "image/pjpeg"):
        raise HTTPException(status_code=415, detail="Only JPEG is supported in Sprint-1")

    # 1) Storage’a yaz + sha256
    stored = await save_upload_to_storage(file, settings.STORAGE_DIR)

    # sha256 unique => aynı dosya ikinci kez yüklenirse 409
    exists = db.query(UploadedDocument).filter(UploadedDocument.file_sha256 == stored.sha256).first()
    if exists:
        raise HTTPException(status_code=409, detail="duplicate file_sha256")

    # 2) DB kaydı aç (status=UPLOADED)
    doc = UploadedDocument(
        user_id=current_user.id,
        customer_id=customer_id,
        receipt_amount_try=None,  # OCR dolduracak
        sender_name=None,
        transfer_date=None,
        original_file_name=file.filename,
        storage_file_name=stored.storage_file_name,
        file_path=stored.file_path,
        mime_type=ct,
        file_size=stored.file_size,
        file_sha256=stored.sha256,
        status=DocumentStatus.UPLOADED.value,
        public_key=_gen_public_key(),
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    write_audit_event(
        db,
        document_id=doc.id,
        event_type="DOCUMENT_UPLOADED",
        actor_type="USER",
        actor_id=str(current_user.id),
        payload={
            "customer_id": str(customer_id),
            "original_file_name": doc.original_file_name,
            "storage_file_name": doc.storage_file_name,
            "file_size": doc.file_size,
            "file_sha256": doc.file_sha256,
        },
    )

    # 3) OCR (sync mock) → alanları yaz
    ocr = parse_receipt_mock(file_path=doc.file_path, original_file_name=doc.original_file_name)

    doc.sender_name = ocr.sender_name
    doc.receipt_amount_try = ocr.amount_try
    doc.transfer_date = ocr.transfer_date
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

    # 4) Telegram’a gönder (env yoksa fail audit yaz)
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

    # response mapping: schema amount_try bekliyor (receipt_amount_try’dan dolduruyoruz)
    return DocumentUploadOut(
        id=doc.id,
        public_key=doc.public_key,
        status=doc.status,
        customer_id=doc.customer_id,
        original_file_name=doc.original_file_name,
        storage_file_name=doc.storage_file_name,
        file_path=doc.file_path,
        mime_type=doc.mime_type,
        file_size=doc.file_size,
        file_sha256=doc.file_sha256,
        sender_name=doc.sender_name,
        amount_try=doc.receipt_amount_try,
        transfer_date=doc.transfer_date,
        tg_chat_id=doc.tg_chat_id,
        tg_message_id=doc.tg_message_id,
        created_at=doc.created_at,
    )