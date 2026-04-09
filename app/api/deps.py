from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core import security
from app.db.session import get_db
from app.services.user_service import UserService
from app.services.group_service import GroupService
from app.services.expense_service import ExpenseService
from app.services.transaction_service import TransactionService
from app.repositories.user_repository import UserRepository
from app.repositories.group_repository import GroupRepository
from app.repositories.expense_repository import ExpenseRepository
from app.repositories.transaction_repository import BalanceRepository, SettlementRepository
from app.repositories.report_repository import ReportRepository
from app.services.report_service import ReportService
from app.models.user import User
from app.schemas.user import TokenData

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

def get_user_service(db: Session = Depends(get_db)) -> UserService:
    repo = UserRepository(db)
    return UserService(repo)

def get_group_service(db: Session = Depends(get_db)) -> GroupService:
    repo = GroupRepository(db)
    user_repo = UserRepository(db)
    return GroupService(repo, user_repo)

def get_expense_service(db: Session = Depends(get_db)) -> ExpenseService:
    repo = ExpenseRepository(db)
    group_repo = GroupRepository(db)
    balance_repo = BalanceRepository(db)
    return ExpenseService(repo, group_repo, balance_repo)

def get_transaction_service(db: Session = Depends(get_db)) -> TransactionService:
    settlement_repo = SettlementRepository(db)
    balance_repo = BalanceRepository(db)
    user_repo = UserRepository(db)
    group_repo = GroupRepository(db)
    return TransactionService(settlement_repo, balance_repo, user_repo, group_repo)

def get_report_service(db: Session = Depends(get_db)) -> ReportService:
    repo = ReportRepository(db)
    return ReportService(repo)

def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[security.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(sub=user_id)
    except JWTError:
        raise credentials_exception

    user_service = UserService(UserRepository(db))
    user = user_service.get_user_by_id(user_id=int(token_data.sub))
    if user is None:
        raise credentials_exception
    return user

def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
