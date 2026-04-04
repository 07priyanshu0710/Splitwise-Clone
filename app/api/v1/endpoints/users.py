from typing import Any
from fastapi import APIRouter, Depends
from app.schemas.user import UserResponse, UserUpdate
from app.models.user import User
from app.api import deps
from app.services.user_service import UserService

router = APIRouter()

@router.get("/me", response_model=UserResponse)
def read_user_me(
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    return current_user

@router.put("/me", response_model=UserResponse)
def update_user_me(
    *,
    user_in: UserUpdate,
    current_user: User = Depends(deps.get_current_active_user),
    service: UserService = Depends(deps.get_user_service)
) -> Any:
    return service.update_user(current_user, user_in)
