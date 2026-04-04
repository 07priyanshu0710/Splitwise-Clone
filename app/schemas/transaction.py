from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.schemas.user import UserResponse
from app.schemas.group import GroupResponse

class SettlementCreate(BaseModel):
    payee_id: int
    amount: float = Field(..., gt=0)
    currency_code: str = Field(default="USD", max_length=10)
    group_id: Optional[int] = None
    description: Optional[str] = None

class SettlementResponse(BaseModel):
    id: int
    payer_id: int
    payee_id: int
    amount: float
    currency_code: str
    group_id: Optional[int] = None
    description: Optional[str] = None
    created_at: datetime
    
    payer: UserResponse
    payee: UserResponse

    class Config:
        from_attributes = True

class BalanceResponse(BaseModel):
    id: int
    user_id: int
    owes_to_id: int
    group_id: Optional[int] = None
    amount: float
    currency_code: str
    last_updated: datetime

    user: Optional[UserResponse] = None
    owes_to: Optional[UserResponse] = None

    class Config:
        from_attributes = True

class GroupBalancesResponse(BaseModel):
    group_id: int
    balances: List[BalanceResponse]

class UserBalancesResponse(BaseModel):
    user_id: int
    balances: List[BalanceResponse]
