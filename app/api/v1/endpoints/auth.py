
from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core import security
from app.schemas.user import UserCreate, UserResponse, Token, UserLogin
from app.services.user_service import UserService
from app.api import deps

router = APIRouter()

@router.post("/register", response_model=UserResponse)
def register(
    *,
    user_in: UserCreate,
    service: UserService = Depends(deps.get_user_service)
) -> Any:
    """
    Create new user.
    """
    return service.register_user(user_in)

@router.post("/login", response_model=Token)
def login_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: UserService = Depends(deps.get_user_service)
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    user_in = UserLogin(email=form_data.username, password=form_data.password)
    return service.authenticate_user(user_in)
