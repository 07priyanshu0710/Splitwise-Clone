from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.expense import SplitType
from app.schemas.user import UserResponse
from app.schemas.group import GroupListResponse

class ExpenseSplitCreate(BaseModel):
    user_id: int
    amount: Optional[float] = None
    percentage: Optional[float] = None
    shares: Optional[float] = None

class ExpenseCreate(BaseModel):
    description: str = Field(..., min_length=1, max_length=255)
    amount: float = Field(..., gt=0)
    curvature_code: str = Field(default="USD", max_length=10)
    group_id: Optional[int] = None
    split_type: SplitType
    splits: List[ExpenseSplitCreate]

class ExpenseSplitResponse(BaseModel):
    id: int
    user_id: int
    amount: Optional[float] = None
    percentage: Optional[float] = None
    shares: Optional[float] = None
    user: UserResponse

    class Config:
        from_attributes = True

class ExpenseResponse(BaseModel):
    id: int
    description: str
    amount: float
    curvature_code: str
    date: datetime
    created_at: datetime
    payer_id: int
    group_id: Optional[int] = None
    split_type: SplitType
    
    payer: UserResponse
    group: Optional[GroupListResponse] = None
    splits: List[ExpenseSplitResponse]

    class Config:
        from_attributes = True
