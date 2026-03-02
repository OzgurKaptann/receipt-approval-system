from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.auth import get_current_user
from app.models.deposit import Deposit
from app.models.enums import DepositStatus
from app.models.user import User
from app.schemas.deposit import DepositCreate, DepositOut

router = APIRouter(prefix="/deposits", tags=["deposits"])


@router.get("", response_model=list[DepositOut])
def list_deposits(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return db.query(Deposit).order_by(Deposit.created_at.desc()).all()


@router.post("", response_model=DepositOut)
def create_deposit(
    payload: DepositCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    dep = Deposit(
        document_id=payload.document_id,
        amount=payload.amount,
        status=DepositStatus.PENDING,
    )
    db.add(dep)
    db.commit()
    db.refresh(dep)
    return dep
