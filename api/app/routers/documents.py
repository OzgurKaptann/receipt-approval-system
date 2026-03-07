import secrets
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.db import get_db
from app.core.settings import settings
from app.models.document import UploadedDocument
from app.models.deposit import Deposit
from app.models.enums import DocumentStatus, DepositStatus
from app.models.user import User
from sqlalchemy import func
from decimal import Decimal
from typing import Optional
from app.schemas.document import DocumentUploadOut, DashboardMetricsOut, DailyInvestmentOut, DocumentListOut
from app.services.audit import write_audit_event
from app.services.storage import save_upload_to_storage
from app.worker import process_document_ocr_task
from app.core.rate_limit import limiter
from fastapi import Request
from fastapi.responses import FileResponse, StreamingResponse
import boto3
import json

router = APIRouter(prefix="/documents", tags=["documents"])


def _gen_public_key() -> str:
    # guess edilemeyecek: uuid4 + token_urlsafe
    return f"{secrets.token_hex(16)}_{secrets.token_urlsafe(16)}"


@router.post("/upload", response_model=DocumentUploadOut)
@limiter.limit("5/minute")
async def upload_document(
    request: Request,
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

    # 3) Async OCR and Telegram message
    process_document_ocr_task.delay(str(doc.id))

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


@router.get("/metrics", response_model=DashboardMetricsOut)
def get_dashboard_metrics(db: Session = Depends(get_db)):
    # Counts
    total_uploaded = db.query(UploadedDocument).count()
    total_approved = db.query(UploadedDocument).filter(UploadedDocument.status == DocumentStatus.SLACK_APPROVED.value).count()
    total_failed = db.query(UploadedDocument).filter(UploadedDocument.status.in_([DocumentStatus.OCR_FAILED.value, DocumentStatus.TG_REJECTED.value, DocumentStatus.SLACK_REJECTED.value, DocumentStatus.DEPOSIT_FAILED.value])).count()
    
    # Financials (Only successful deposits)
    res = db.query(
        func.sum(Deposit.amount_try).label("total_try"),
        func.sum(Deposit.amount_usd).label("total_usd")
    ).filter(Deposit.status == DepositStatus.DEPOSIT_SUCCESS.value).first()

    sum_try = res.total_try if res and res.total_try else Decimal("0.0")
    sum_usd = res.total_usd if res and res.total_usd else Decimal("0.0")

    rate = (total_approved / total_uploaded * 100) if total_uploaded > 0 else 0.0

    return DashboardMetricsOut(
        total_uploaded=total_uploaded,
        total_approved=total_approved,
        total_failed=total_failed,
        total_try_volume=sum_try,
        total_usd_volume=sum_usd,
        success_rate=round(rate, 2)
    )

@router.get("/daily-investments", response_model=list[DailyInvestmentOut])
def get_daily_investments(db: Session = Depends(get_db)):
    """
    Returns day-by-day aggregations of successful investments for charts and Slack commands.
    """
    # Group by the date of successful deposit creation
    import sqlalchemy
    
    # Cast to date to group by day
    date_field = sqlalchemy.cast(Deposit.created_at, sqlalchemy.Date)
    
    results = db.query(
        date_field.label("day"),
        func.sum(Deposit.amount_try).label("day_try"),
        func.sum(Deposit.amount_usd).label("day_usd"),
        func.count(Deposit.id).label("day_count")
    ).filter(
        Deposit.status == DepositStatus.DEPOSIT_SUCCESS.value
    ).group_by(date_field).order_by(date_field.desc()).limit(30).all()

    out = []
    for r in results:
        out.append(DailyInvestmentOut(
            date=r.day.isoformat(),
            amount_try=r.day_try or Decimal("0.0"),
            amount_usd=r.day_usd or Decimal("0.0"),
            count=r.day_count or 0
        ))
    
    return out

@router.get("", response_model=DocumentListOut)
def list_documents(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    query = db.query(UploadedDocument)
    
    if status:
        query = query.filter(UploadedDocument.status == status)
        
    total = query.count()
    items = query.order_by(UploadedDocument.created_at.desc()).offset(offset).limit(limit).all()
    
    return DocumentListOut(items=items, total=total)


from app.schemas.document import DocumentDetailOut
from app.services.workflow import on_manual_action

@router.get("/{document_id}", response_model=DocumentDetailOut)
def get_document_detail(
    document_id: UUID,
    db: Session = Depends(get_db)
):
    doc = db.query(UploadedDocument).filter(UploadedDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    return DocumentDetailOut.model_validate(doc)


@router.get("/{document_id}/image")
def get_document_image(
    document_id: UUID,
    db: Session = Depends(get_db)
):
    doc = db.query(UploadedDocument).filter(UploadedDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if doc.file_path.startswith("s3://"):
        try:
            s3 = boto3.client(
                "s3",
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION_NAME
            )
            # Fetch object directly as stream
            response = s3.get_object(Bucket=settings.AWS_S3_BUCKET_NAME, Key=doc.storage_file_name)
            return StreamingResponse(
                content=response['Body'],
                media_type=doc.mime_type
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch from S3: {str(e)}")
    else:
        # local FileResponse
        import os
        if not os.path.exists(doc.file_path):
            raise HTTPException(status_code=404, detail="File actually missing on disk")
        return FileResponse(doc.file_path, media_type=doc.mime_type)


@router.post("/{document_id}/approve", response_model=DocumentDetailOut)
def manual_approve_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        doc, _ = on_manual_action(
            db,
            document_id=document_id,
            action="approve",
            actor_id=str(current_user.id)
        )
        return DocumentDetailOut.model_validate(doc)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{document_id}/reject", response_model=DocumentDetailOut)
def manual_reject_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        doc, _ = on_manual_action(
            db,
            document_id=document_id,
            action="reject",
            actor_id=str(current_user.id)
        )
        return DocumentDetailOut.model_validate(doc)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))