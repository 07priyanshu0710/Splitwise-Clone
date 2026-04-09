from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.models.group import GroupMemberRole
from app.schemas.user import UserResponse

class GroupCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None

class GroupUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None

class GroupMemberAdd(BaseModel):
    identifier: str = Field(..., description="Email address or mobile number of the user to add")

class GroupMemberResponse(BaseModel):
    id: int
    user_id: int
    role: GroupMemberRole
    joined_at: datetime
    user: UserResponse

    model_config = ConfigDict(from_attributes=True)

class GroupResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_by_id: int
    created_at: datetime
    members: List[GroupMemberResponse] = []

    model_config = ConfigDict(from_attributes=True)

class GroupListResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_by_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
