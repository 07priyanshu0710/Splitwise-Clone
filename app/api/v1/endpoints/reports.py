from typing import Any, List, Dict
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.models.user import User
from app.models.expense import Expense, ExpenseSplit
from app.api import deps
from pydantic import BaseModel

router = APIRouter()

class MonthlySummaryResponse(BaseModel):
    month: str
    total_paid: float
    total_owed: float

@router.get("/monthly-summary", response_model=List[MonthlySummaryResponse])
def get_monthly_summary(
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Returns a monthly summary of total money paid vs total money owed by the user.
    """
    # 1. Total Paid per month (where user is the payer)
    paid_query = db.query(
        func.to_char(Expense.date, 'YYYY-MM').label('month'),
        func.sum(Expense.amount).label('total_paid')
    ).filter(
        Expense.payer_id == current_user.id
    ).group_by('month').all()

    # 2. Total Owed per month (where user is part of splits but didn't pay the whole thing)
    # We sum the split amounts for the user.
    owed_query = db.query(
        func.to_char(Expense.date, 'YYYY-MM').label('month'),
        func.sum(ExpenseSplit.amount).label('total_owed')
    ).join(Expense, ExpenseSplit.expense_id == Expense.id).filter(
        ExpenseSplit.user_id == current_user.id
    ).group_by('month').all()

    summary_map: Dict[str, dict] = {}
    
    for row in paid_query:
        month = row.month
        summary_map.setdefault(month, {"month": month, "total_paid": 0.0, "total_owed": 0.0})
        summary_map[month]["total_paid"] = float(row.total_paid or 0.0)
        
    for row in owed_query:
        month = row.month
        summary_map.setdefault(month, {"month": month, "total_paid": 0.0, "total_owed": 0.0})
        summary_map[month]["total_owed"] = float(row.total_owed or 0.0)

    # Sort descending by month
    results = sorted(list(summary_map.values()), key=lambda x: x["month"], reverse=True)
    return results
