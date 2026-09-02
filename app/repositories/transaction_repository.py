from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, text
from typing import List, Optional
from decimal import Decimal

from app.repositories.base import BaseRepository
from app.models.transaction import Settlement, Balance
from app.schemas.transaction import BalanceResponse
from app.core.constants import INR_CURRENCY_CODE

class SettlementRepository(BaseRepository[Settlement]):
    def __init__(self, db: Session):
        super().__init__(Settlement, db)

    def create_settlement(self, obj_in: dict, payer_id: int) -> Settlement:
        db_obj = Settlement(**obj_in, payer_id=payer_id)
        self.db.add(db_obj)
        self.db.flush()
        return db_obj

    def get_group_settlements(self, group_id: int) -> List[Settlement]:
        return self.db.query(Settlement).options(
            joinedload(Settlement.payer),
            joinedload(Settlement.payee),
        ).filter(
            Settlement.group_id == group_id,
        ).order_by(
            Settlement.created_at.desc(),
            Settlement.id.desc(),
        ).all()

class BalanceRepository(BaseRepository[Balance]):
    def __init__(self, db: Session):
        super().__init__(Balance, db)

    def get_user_balances(self, user_id: int) -> List[BalanceResponse]:
        balances = self.db.query(Balance).options(
            joinedload(Balance.user),
            joinedload(Balance.owes_to)
        ).filter(
            or_(Balance.user_id == user_id, Balance.owes_to_id == user_id)
        ).all()
        
        return [BalanceResponse.model_validate(balance) for balance in balances]

    def get_group_balances(self, group_id: int) -> List[BalanceResponse]:
        balances = self.db.query(Balance).options(
            joinedload(Balance.user),
            joinedload(Balance.owes_to)
        ).filter(Balance.group_id == group_id).all()
        
        return [BalanceResponse.model_validate(balance) for balance in balances]

    def update_balance(self, user_id: int, owes_to_id: int, amount: float, group_id: Optional[int] = None):
        if user_id == owes_to_id:
            return

        amount_to_process = Decimal(str(amount))
        if amount_to_process <= 0:
            raise ValueError("Balance updates must be positive")

        self._lock_balance_pair(user_id, owes_to_id, group_id)

        reverse_q = self.db.query(Balance).filter(
            Balance.user_id == owes_to_id,
            Balance.owes_to_id == user_id,
        )
        if group_id is not None:
            reverse_q = reverse_q.filter(Balance.group_id == group_id)
        else:
            reverse_q = reverse_q.filter(Balance.group_id.is_(None))

        reverse_balance = reverse_q.with_for_update().first()

        if reverse_balance:
            reverse_amt = Decimal(str(reverse_balance.amount))
            if reverse_amt > amount_to_process:
                reverse_balance.amount = reverse_amt - amount_to_process
            elif reverse_amt == amount_to_process:
                self.db.delete(reverse_balance)
            else:
                amount_to_process -= reverse_amt
                self.db.delete(reverse_balance)
                self.db.flush()
                self._update_direct_balance(user_id, owes_to_id, amount_to_process, group_id)
        else:
            self._update_direct_balance(user_id, owes_to_id, amount_to_process, group_id)
        
        self.db.flush()

    def get_outstanding_debt_for_update(
        self,
        debtor_id: int,
        creditor_id: int,
        group_id: Optional[int] = None,
    ) -> Optional[Balance]:
        self._lock_balance_pair(debtor_id, creditor_id, group_id)

        query = self.db.query(Balance).filter(
            Balance.user_id == debtor_id,
            Balance.owes_to_id == creditor_id,
        )
        if group_id is None:
            query = query.filter(Balance.group_id.is_(None))
        else:
            query = query.filter(Balance.group_id == group_id)
        return query.with_for_update().first()

    def reduce_outstanding_debt(self, balance: Balance, amount: Decimal) -> None:
        outstanding = Decimal(str(balance.amount))
        if amount <= 0 or amount > outstanding:
            raise ValueError("Settlement amount must be within the outstanding debt")

        if amount == outstanding:
            self.db.delete(balance)
        else:
            balance.amount = outstanding - amount
        self.db.flush()

    def _lock_balance_pair(
        self,
        first_user_id: int,
        second_user_id: int,
        group_id: Optional[int],
    ) -> None:
        first_user_id, second_user_id = sorted((first_user_id, second_user_id))
        lock_key = f"balance:{first_user_id}:{second_user_id}:{group_id}"
        self.db.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:lock_key, 0))"),
            {"lock_key": lock_key},
        )

    def _update_direct_balance(self, user_id, owes_to_id, amount_to_process, group_id):
        direct_q = self.db.query(Balance).filter(
            Balance.user_id == user_id,
            Balance.owes_to_id == owes_to_id,
        )
        if group_id is not None:
            direct_q = direct_q.filter(Balance.group_id == group_id)
        else:
            direct_q = direct_q.filter(Balance.group_id.is_(None))

        direct_balance = direct_q.with_for_update().first()

        if direct_balance:
            direct_amt = Decimal(str(direct_balance.amount))
            direct_balance.amount = direct_amt + amount_to_process
        else:
            new_balance = Balance(
                user_id=user_id,
                owes_to_id=owes_to_id,
                amount=amount_to_process,
                currency_code=INR_CURRENCY_CODE,
                group_id=group_id
            )
            self.db.add(new_balance)
