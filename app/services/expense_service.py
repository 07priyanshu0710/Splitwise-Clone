from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List
from decimal import Decimal

from app.repositories.expense_repository import ExpenseRepository
from app.repositories.group_repository import GroupRepository
from app.repositories.transaction_repository import BalanceRepository
from app.schemas.expense import ExpenseCreate
from app.models.expense import Expense, SplitType
from app.models.user import User

class ExpenseService:
    def __init__(self, db: Session):
        self.repository = ExpenseRepository(db)
        self.group_repository = GroupRepository(db)
        self.balance_repository = BalanceRepository(db)

    def create_expense(self, expense_in: ExpenseCreate, current_user: User) -> Expense:
        if expense_in.group_id is not None:
            member = self.group_repository.get_member(expense_in.group_id, current_user.id)
            if not member:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only add expenses to groups you are in")

        if not expense_in.splits:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one split must be provided")

        total_amount = Decimal(str(expense_in.amount))

        if expense_in.split_type == SplitType.EQUAL:
            self._validate_equal_split(total_amount, expense_in.splits)
        elif expense_in.split_type == SplitType.UNEQUAL:
            self._validate_unequal_split(total_amount, expense_in.splits)
        elif expense_in.split_type == SplitType.PERCENTAGE:
            self._validate_percentage_split(total_amount, expense_in.splits)
        elif expense_in.split_type == SplitType.SHARE:
            self._validate_share_split(total_amount, expense_in.splits)
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid split type")

        expense_data = expense_in.model_dump(exclude={'splits'})
        splits_data = [split.model_dump() for split in expense_in.splits]
        expense = self.repository.create_with_splits(expense_data, splits_data, current_user.id)

        for split in expense.splits:
            if split.user_id != expense.payer_id and split.amount > 0:
                self.balance_repository.update_balance(
                    user_id=split.user_id,
                    owes_to_id=expense.payer_id,
                    amount=split.amount,
                    currency_code=expense.curvature_code,
                    group_id=expense.group_id
                )

        return self.repository.get_with_details(expense.id)

    def _validate_equal_split(self, total: Decimal, splits: List):
        count = len(splits)
        split_amount = round(total / count, 2)
        remainder = total - (split_amount * count)

        for i, split in enumerate(splits):
            if i == 0:
                split.amount = float(split_amount + remainder)
            else:
                split.amount = float(split_amount)
            split.percentage = None
            split.shares = None

    def _validate_unequal_split(self, total: Decimal, splits: List):
        split_sum = Decimal('0.00')
        for split in splits:
            if split.amount is None:
                raise HTTPException(status_code=400, detail="Amount must be provided for unequal split")
            split_sum += Decimal(str(split.amount))
            split.percentage = None
            split.shares = None

        if split_sum != total:
            raise HTTPException(status_code=400, detail=f"Sum of splits ({split_sum}) does not equal total amount ({total})")

    def _validate_percentage_split(self, total: Decimal, splits: List):
        perc_sum = Decimal('0.00')
        calculated_sum = Decimal('0.00')
        for split in splits:
            if split.percentage is None:
                raise HTTPException(status_code=400, detail="Percentage must be provided for percentage split")
            perc = Decimal(str(split.percentage))
            perc_sum += perc
            amt = round(total * perc / Decimal('100'), 2)
            split.amount = float(amt)
            calculated_sum += amt
            split.shares = None

        if perc_sum != Decimal('100.00'):
            raise HTTPException(status_code=400, detail=f"Sum of percentages ({perc_sum}) does not equal 100")

        remainder = total - calculated_sum
        splits[0].amount = float(Decimal(str(splits[0].amount)) + remainder)

    def _validate_share_split(self, total: Decimal, splits: List):
        total_shares = Decimal('0')
        for split in splits:
            if split.shares is None:
                raise HTTPException(status_code=400, detail="Shares must be provided for share split")
            total_shares += Decimal(str(split.shares))
            split.percentage = None

        if total_shares <= 0:
            raise HTTPException(status_code=400, detail="Total shares must be greater than zero")

        calculated_sum = Decimal('0.00')
        for split in splits:
            shares = Decimal(str(split.shares))
            amt = round(total * shares / total_shares, 2)
            split.amount = float(amt)
            calculated_sum += amt

        remainder = total - calculated_sum
        splits[0].amount = float(Decimal(str(splits[0].amount)) + remainder)

    def get_expense(self, expense_id: int, user_id: int) -> Expense:
        expense = self.repository.get_with_details(expense_id)
        if not expense:
            raise HTTPException(status_code=404, detail="Expense not found")
        if expense.payer_id != user_id and not any(s.user_id == user_id for s in expense.splits):
            raise HTTPException(status_code=403, detail="Forbidden")
        return expense

    def get_group_expenses(self, group_id: int, user_id: int) -> List[Expense]:
        member = self.group_repository.get_member(group_id, user_id)
        if not member:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this group")
        return self.repository.get_group_expenses(group_id)
