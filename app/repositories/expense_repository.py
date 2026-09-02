from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from app.repositories.base import BaseRepository
from app.models.expense import Expense, ExpenseSplit
from app.schemas.expense import ExpenseCreate

# Expense doesn't easily map to the generic update model for now, so we will not pass UpdateSchema
class ExpenseRepository(BaseRepository[Expense]):
    def __init__(self, db: Session):
        super().__init__(Expense, db)

    def get_with_details(self, id: int) -> Optional[Expense]:
        return self.db.query(self.model).options(
            joinedload(Expense.payer),
            joinedload(Expense.group),
            joinedload(Expense.splits).joinedload(ExpenseSplit.user)
        ).filter(self.model.id == id).first()

    def get_group_expenses(self, group_id: int) -> List[Expense]:
        return self.db.query(self.model).options(
            joinedload(Expense.payer),
            joinedload(Expense.splits).joinedload(ExpenseSplit.user)
        ).filter(self.model.group_id == group_id).all()

    def create_with_splits(self, obj_in: dict, splits_in: List[dict], user_id: int) -> Expense:
        db_obj = Expense(**obj_in, payer_id=user_id)
        self.db.add(db_obj)

        for split_data in splits_in:
            db_obj.splits.append(ExpenseSplit(**split_data))

        self.db.flush()
        return db_obj
