from typing import Any, List
from fastapi import APIRouter, Depends
from app.schemas.transaction import BalanceResponse
from app.models.user import User
from app.api import deps
from app.services.transaction_service import TransactionService

router = APIRouter()

@router.get("/group/{group_id}", response_model=List[BalanceResponse])
def get_group_balances(
    group_id: int,
    current_user: User = Depends(deps.get_current_active_user),
    service: TransactionService = Depends(deps.get_transaction_service)
) -> Any:
    return service.get_group_balances(group_id, current_user)

@router.get("/me", response_model=List[BalanceResponse])
def get_user_balances(
    current_user: User = Depends(deps.get_current_active_user),
    service: TransactionService = Depends(deps.get_transaction_service)
) -> Any:
    return service.get_user_balances(current_user)
