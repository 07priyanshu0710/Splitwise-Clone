from typing import Optional, Any
import logging

from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserLogin, Token
from app.core import security
from app.models.user import User
from app.core.exceptions import BusinessLogicError, UnauthorizedError
from app.core.logging_config import LoggerMixin

class UserService(LoggerMixin):
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def register_user(self, user_in: UserCreate) -> User:
        if self.repository.get_by_email(user_in.email):
            raise BusinessLogicError("Email already registered")

        if user_in.mobile_number and self.repository.get_by_mobile_number(user_in.mobile_number):
            raise BusinessLogicError("Mobile number already registered")

        hashed_password = security.get_password_hash(user_in.password)
        user_data = user_in.model_dump()
        user_data["hashed_password"] = hashed_password
        del user_data["password"]

        user = self.repository.create(user_data)
        self.logger.info(f"User {user.email} registered successfully")
        return user

    def authenticate_user(self, user_in: UserLogin) -> Token:
        user = self.repository.get_by_email(user_in.email)
        if not user or not security.verify_password(user_in.password, user.hashed_password):
            self.logger.warning(f"Failed login attempt for email: {user_in.email}")
            raise UnauthorizedError("Incorrect email or password")

        access_token = security.create_access_token(subject=user.id)
        self.logger.info(f"User {user.email} authenticated")
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
