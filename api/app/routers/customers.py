from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.db import get_db
from app.core.auth import get_current_user
from app.models.customer import Customer
from app.models.user import User
from app.schemas.customer import CustomerCreate, CustomerOut

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("", response_model=list[CustomerOut])
def list_customers(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Return only customers that belong to the authenticated user.
    Prevents cross-user data leakage.
    """
    query = db.query(Customer).filter(Customer.user_id == user.id)

    if hasattr(Customer, "created_at"):
        return query.order_by(Customer.created_at.desc()).all()

    return query.order_by(Customer.id.desc()).all()


@router.post("", response_model=CustomerOut)
def create_customer(
    payload: CustomerCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Create a new customer bound to the authenticated user.
    Enforces DB uniqueness constraints safely.
    """
    customer = Customer(
        user_id=user.id,
        crm_customer_id=payload.crm_customer_id,
        mt_account_id=payload.mt_account_id,
        mt_currency=payload.mt_currency,
    )

    db.add(customer)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="CRM customer ID or MT account ID already exists.",
        )

    db.refresh(customer)
    return customer