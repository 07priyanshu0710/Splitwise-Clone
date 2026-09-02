from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Literal
from datetime import datetime
from app.models.expense import SplitType
from app.schemas.user import UserResponse
from app.schemas.group import GroupListResponse
from app.core.constants import INR_CURRENCY_CODE

class ExpenseSplitCreate(BaseModel):
    user_id: int
    amount: Optional[float] = Field(default=None, ge=0, allow_inf_nan=False)
    percentage: Optional[float] = Field(default=None, ge=0, le=100, allow_inf_nan=False)
    shares: Optional[float] = Field(default=None, ge=0, allow_inf_nan=False)

class ExpenseCreate(BaseModel):
    description: str = Field(..., min_length=1, max_length=255)
    amount: float = Field(..., gt=0, allow_inf_nan=False)
    curvature_code: Literal["INR"] = INR_CURRENCY_CODE
    group_id: Optional[int] = None
    split_type: SplitType
    splits: List[ExpenseSplitCreate] = Field(..., min_length=1)

class ExpenseSplitResponse(BaseModel):
    id: int
    user_id: int
    amount: Optional[float] = None
    percentage: Optional[float] = None
    shares: Optional[float] = None
    user: UserResponse

    model_config = ConfigDict(from_attributes=True)

class ExpenseResponse(BaseModel):
    id: int
    description: str
    amount: float
    curvature_code: Literal["INR"]
    date: datetime
    created_at: datetime
    payer_id: int
    group_id: Optional[int] = None
    split_type: SplitType
    
    payer: UserResponse
    group: Optional[GroupListResponse] = None
    splits: List[ExpenseSplitResponse]

    model_config = ConfigDict(from_attributes=True)
