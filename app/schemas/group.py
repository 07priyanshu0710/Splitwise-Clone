from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.group import GroupMemberRole
from app.schemas.user import UserResponse

# Properties to receive via API on creation
class GroupCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None

# Properties to receive via API on update
class GroupUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None

class GroupMemberAdd(BaseModel):
    email: str

class GroupMemberResponse(BaseModel):
    id: int
    user_id: int
    role: GroupMemberRole
    joined_at: datetime
    user: UserResponse

    class Config:
        from_attributes = True

# Properties to return via API
class GroupResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_by_id: int
    created_at: datetime
    members: List[GroupMemberResponse] = []

    class Config:
        from_attributes = True

class GroupListResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_by_id: int
    created_at: datetime

    class Config:
        from_attributes = True
