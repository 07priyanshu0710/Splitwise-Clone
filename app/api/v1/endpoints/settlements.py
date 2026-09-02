from typing import Any, List
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
    return service.create_settlement(settlement_in, current_user)


@router.get("/group/{group_id}", response_model=List[SettlementResponse])
def get_group_settlements(
    group_id: int,
    current_user: User = Depends(deps.get_current_active_user),
    service: TransactionService = Depends(deps.get_transaction_service),
) -> Any:
    return service.get_group_settlements(group_id, current_user)
