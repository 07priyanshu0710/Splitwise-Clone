from typing import Any
from fastapi import APIRouter, Depends
from app.schemas.transaction import SettlementResponse, SettlementCreate
from app.models.user import User
from app.api import deps
from app.services.transaction_service import TransactionService

router = APIRouter()

@router.post("/", response_model=SettlementResponse)
def create_settlement(
    *,
    settlement_in: SettlementCreate,
    current_user: User = Depends(deps.get_current_active_user),
    service: TransactionService = Depends(deps.get_transaction_service)
) -> Any:
    """
    Record a payment (settlement) from the current user to someone else.
    """
    return service.create_settlement(settlement_in, current_user)
