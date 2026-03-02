from fastapi import APIRouter, Depends
from app.core.auth import get_current_user
from app.models.user import User

router = APIRouter(tags=["me"])

@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {"id": str(user.id), "email": user.email, "full_name": user.full_name, "is_active": user.is_active}
