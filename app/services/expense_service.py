from typing import List
from decimal import Decimal

from app.repositories.expense_repository import ExpenseRepository
from app.repositories.group_repository import GroupRepository
from app.repositories.transaction_repository import BalanceRepository
from app.repositories.audit_repository import AuditRepository
from app.schemas.expense import ExpenseCreate
from app.models.expense import Expense, SplitType
from app.models.user import User
from app.core.exceptions import BusinessLogicError, NotFoundError, ForbiddenError
from app.core.constants import INR_CURRENCY_CODE
from app.core.logging_config import LoggerMixin

class ExpenseService(LoggerMixin):
    def __init__(
        self, 
        repository: ExpenseRepository, 
        group_repository: GroupRepository, 
        balance_repository: BalanceRepository,
        audit_repository: AuditRepository,
    ):
        self.repository = repository
        self.group_repository = group_repository
        self.balance_repository = balance_repository
        self.audit_repository = audit_repository

    def create_expense(self, expense_in: ExpenseCreate, current_user: User) -> Expense:
        self.logger.info(f"Creating expense: {expense_in.description} for user {current_user.id}")

        split_user_ids = [split.user_id for split in expense_in.splits]
        if len(split_user_ids) != len(set(split_user_ids)):
            raise BusinessLogicError("Each user can appear only once in an expense split")
        
        if expense_in.group_id is not None:
            member = self.group_repository.get_member(expense_in.group_id, current_user.id)
            if not member:
                self.logger.warning(f"User {current_user.id} tried to add expense to group {expense_in.group_id} they are not in")
                raise ForbiddenError("You can only add expenses to groups you are in")
            member_user_ids = self.group_repository.get_member_user_ids(
                expense_in.group_id,
                set(split_user_ids),
            )
            invalid_user_ids = set(split_user_ids) - member_user_ids
            if invalid_user_ids:
                raise ForbiddenError("All expense participants must be members of the group")

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
            raise BusinessLogicError("Invalid split type")

        expense_data = expense_in.model_dump(exclude={'splits'})
        splits_data = [split.model_dump() for split in expense_in.splits]
        
        try:
            expense = self.repository.create_with_splits(expense_data, splits_data, current_user.id)

            balance_updates = [
                split for split in expense.splits
                if split.user_id != expense.payer_id and split.amount > 0
            ]
            for split in sorted(balance_updates, key=lambda item: item.user_id):
                self.balance_repository.update_balance(
                    user_id=split.user_id,
                    owes_to_id=expense.payer_id,
                    amount=split.amount,
                    group_id=expense.group_id
                )

            self.audit_repository.record(
                action="expense.created",
                entity_type="expense",
                entity_id=expense.id,
                user_id=current_user.id,
                changes={
                    "group_id": expense.group_id,
                    "payer_id": expense.payer_id,
                    "amount": f"{Decimal(str(expense.amount)):.2f}",
                    "currency_code": INR_CURRENCY_CODE,
                    "split_type": expense.split_type.value,
                    "participant_ids": sorted(split_user_ids),
                },
            )

            expense_id = expense.id
            payer_id = expense.payer_id
            group_id = expense.group_id
            self.repository.db.commit()
            for split in balance_updates:
                self.balance_repository.invalidate_balance_cache(
                    split.user_id,
                    payer_id,
                    group_id,
                )
        except Exception as e:
            self.repository.db.rollback()
            self.logger.exception(f"Failed to create expense: {str(e)}")
            raise BusinessLogicError("Failed to create expense") from e

        self.logger.info(f"Expense {expense_id} created successfully")
        return self.repository.get_with_details(expense_id)

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
                raise BusinessLogicError("Amount must be provided for unequal split")
            split_sum += Decimal(str(split.amount))
            split.percentage = None
            split.shares = None

        if split_sum != total:
            raise BusinessLogicError(f"Sum of splits ({split_sum}) does not equal total amount ({total})")

    def _validate_percentage_split(self, total: Decimal, splits: List):
        perc_sum = Decimal('0.00')
        calculated_sum = Decimal('0.00')
        for split in splits:
            if split.percentage is None:
                raise BusinessLogicError("Percentage must be provided for percentage split")
            perc = Decimal(str(split.percentage))
            perc_sum += perc
            amt = round(total * perc / Decimal('100'), 2)
            split.amount = float(amt)
            calculated_sum += amt
            split.shares = None

        if perc_sum != Decimal('100.00'):
            raise BusinessLogicError(f"Sum of percentages ({perc_sum}) does not equal 100")

        remainder = total - calculated_sum
        splits[0].amount = float(Decimal(str(splits[0].amount)) + remainder)

    def _validate_share_split(self, total: Decimal, splits: List):
        total_shares = Decimal('0')
        for split in splits:
            if split.shares is None:
                raise BusinessLogicError("Shares must be provided for share split")
            total_shares += Decimal(str(split.shares))
            split.percentage = None

        if total_shares <= 0:
            raise BusinessLogicError("Total shares must be greater than zero")

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
            raise NotFoundError("Expense not found")
        if expense.payer_id != user_id and not any(s.user_id == user_id for s in expense.splits):
            raise ForbiddenError("You do not have access to this expense")
        return expense

    def get_group_expenses(self, group_id: int, user_id: int) -> List[Expense]:
        member = self.group_repository.get_member(group_id, user_id)
        if not member:
            raise ForbiddenError("Not a member of this group")
        return self.repository.get_group_expenses(group_id)
