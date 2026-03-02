from pydantic import BaseModel, Field
from uuid import UUID

class CustomerCreate(BaseModel):
    crm_customer_id: str = Field(min_length=1, max_length=80)
    mt_account_id: str = Field(min_length=1, max_length=80)
    mt_currency: str = Field(min_length=3, max_length=3)

class CustomerOut(BaseModel):
    id: UUID
    user_id: UUID | None
    crm_customer_id: str
    mt_account_id: str
    mt_currency: str

    model_config = {"from_attributes": True}