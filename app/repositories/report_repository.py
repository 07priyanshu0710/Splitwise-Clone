from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict
from app.models.expense import Expense, ExpenseSplit

class ReportRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_monthly_summary(self, user_id: int) -> List[dict]:
        paid_query = self.db.query(
            func.to_char(Expense.date, 'YYYY-MM').label('month'),
            func.sum(Expense.amount).label('total_paid')
        ).filter(
            Expense.payer_id == user_id
        ).group_by('month').all()

        owed_query = self.db.query(
            func.to_char(Expense.date, 'YYYY-MM').label('month'),
            func.sum(ExpenseSplit.amount).label('total_owed')
        ).join(Expense, ExpenseSplit.expense_id == Expense.id).filter(
            ExpenseSplit.user_id == user_id
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

        return sorted(list(summary_map.values()), key=lambda x: x["month"], reverse=True)
