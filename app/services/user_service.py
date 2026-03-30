
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import Optional, Any

from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserLogin, Token
from app.core import security
from app.models.user import User

class UserService:
    def __init__(self, db: Session):
        self.repository = UserRepository(db)

    def register_user(self, user_in: UserCreate) -> User:
        # Check if user exists
        if self.repository.get_by_email(user_in.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        
        # Hash password and create user
        hashed_password = security.get_password_hash(user_in.password)
        user_data = user_in.model_dump()
        user_data["hashed_password"] = hashed_password
        del user_data["password"]
        
        return self.repository.create(user_data)

    def authenticate_user(self, user_in: UserLogin) -> Token:
        user = self.repository.get_by_email(user_in.email)
        if not user or not security.verify_password(user_in.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token = security.create_access_token(subject=user.id)
        return Token(access_token=access_token, token_type="bearer")

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        return self.repository.get(user_id)

    def update_user(self, user: User, user_in: Any) -> User:
        user_data = user_in.model_dump(exclude_unset=True)
        if "password" in user_data and user_data["password"]:
            hashed_password = security.get_password_hash(user_data["password"])
            user_data["hashed_password"] = hashed_password
            del user_data["password"]
        
        return self.repository.update(user, user_data)
