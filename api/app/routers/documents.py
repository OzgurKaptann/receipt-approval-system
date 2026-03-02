from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.auth import get_current_user
from app.models.document import UploadedDocument
from app.models.user import User
from app.schemas.document import DocumentCreate, DocumentOut

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=list[DocumentOut])
def list_documents(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return db.query(UploadedDocument).order_by(UploadedDocument.created_at.desc()).all()


@router.post("", response_model=DocumentOut)
def create_document(
    payload: DocumentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    d = UploadedDocument(
        customer_id=payload.customer_id,
        file_name=payload.file_name,
        mime_type=payload.mime_type,
        storage_path=payload.storage_path,
    )
    db.add(d)
    db.commit()
    db.refresh(d)
    return d
