from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Literal
from datetime import datetime
from app.schemas.user import UserResponse
from app.core.constants import INR_CURRENCY_CODE

class BalanceResponse(BaseModel):
    id: int
    user_id: int
    owes_to_id: int
    group_id: Optional[int] = None
    amount: float
    currency_code: Literal["INR"]
    last_updated: datetime

    user: Optional[UserResponse] = None
    owes_to: Optional[UserResponse] = None

    model_config = ConfigDict(from_attributes=True)

class SettlementCreate(BaseModel):
    payee_id: int
    amount: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)
    currency_code: Literal["INR"] = INR_CURRENCY_CODE
    group_id: Optional[int] = None
    description: Optional[str] = None

class SettlementResponse(BaseModel):
    id: int
    payer_id: int
    payee_id: int
    amount: float
    currency_code: Literal["INR"]
    group_id: Optional[int] = None
    description: Optional[str] = None
    created_at: datetime

    payer: UserResponse
    payee: UserResponse

    model_config = ConfigDict(from_attributes=True)

class GroupBalancesResponse(BaseModel):
    group_id: int
    balances: List[BalanceResponse]

class UserBalancesResponse(BaseModel):
    user_id: int
    balances: List[BalanceResponse]
