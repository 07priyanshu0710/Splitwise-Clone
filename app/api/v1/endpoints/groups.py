from typing import Any, List
from fastapi import APIRouter, Depends
from app.schemas.group import GroupResponse, GroupCreate, GroupMemberAdd, GroupListResponse
from app.models.user import User
from app.api import deps
from app.services.group_service import GroupService

router = APIRouter()

@router.post("/", response_model=GroupResponse)
def create_group(
    *,
    group_in: GroupCreate,
    current_user: User = Depends(deps.get_current_active_user),
    service: GroupService = Depends(deps.get_group_service)
) -> Any:
    return service.create_group(group_in, current_user.id)

@router.get("/", response_model=List[GroupListResponse])
def get_user_groups(
    current_user: User = Depends(deps.get_current_active_user),
    service: GroupService = Depends(deps.get_group_service)
) -> Any:
    return service.get_user_groups(current_user.id)

@router.get("/{group_id}", response_model=GroupResponse)
def get_group(
    group_id: int,
    current_user: User = Depends(deps.get_current_active_user),
    service: GroupService = Depends(deps.get_group_service)
) -> Any:
    return service.get_group(group_id, current_user.id)

@router.post("/{group_id}/members", response_model=GroupResponse)
def add_group_member(
    group_id: int,
    *,
    member_in: GroupMemberAdd,
    current_user: User = Depends(deps.get_current_active_user),
    service: GroupService = Depends(deps.get_group_service)
) -> Any:
    return service.add_member(group_id, member_in, current_user.id)
