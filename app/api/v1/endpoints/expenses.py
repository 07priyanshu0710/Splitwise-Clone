from typing import Any, List
from fastapi import APIRouter, Depends
from app.schemas.expense import ExpenseResponse, ExpenseCreate
from app.models.user import User
from app.api import deps
from app.services.expense_service import ExpenseService

router = APIRouter()

@router.post("/", response_model=ExpenseResponse)
def create_expense(
    *,
    expense_in: ExpenseCreate,
    current_user: User = Depends(deps.get_current_active_user),
    service: ExpenseService = Depends(deps.get_expense_service)
) -> Any:
    return service.create_expense(expense_in, current_user)

@router.get("/{expense_id}", response_model=ExpenseResponse)
def get_expense(
    expense_id: int,
    current_user: User = Depends(deps.get_current_active_user),
    service: ExpenseService = Depends(deps.get_expense_service)
) -> Any:
    return service.get_expense(expense_id, current_user.id)

@router.get("/group/{group_id}", response_model=List[ExpenseResponse])
def get_group_expenses(
    group_id: int,
    current_user: User = Depends(deps.get_current_active_user),
    service: ExpenseService = Depends(deps.get_expense_service)
) -> Any:
    return service.get_group_expenses(group_id, current_user.id)
