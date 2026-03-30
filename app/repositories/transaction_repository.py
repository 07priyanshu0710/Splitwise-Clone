from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_
from typing import List, Optional
from decimal import Decimal

from app.repositories.base import BaseRepository
from app.models.transaction import Settlement, Balance
from app.schemas.transaction import SettlementCreate

class SettlementRepository(BaseRepository[Settlement]):
    def __init__(self, db: Session):
        super().__init__(Settlement, db)

    def create_settlement(self, obj_in: dict, payer_id: int) -> Settlement:
        db_obj = Settlement(**obj_in)
        db_obj.payer_id = payer_id
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

class BalanceRepository(BaseRepository[Balance]):
    def __init__(self, db: Session):
        super().__init__(Balance, db)

    def get_user_balances(self, user_id: int) -> List[Balance]:
        return self.db.query(Balance).filter(
            or_(Balance.user_id == user_id, Balance.owes_to_id == user_id)
        ).all()

    def get_group_balances(self, group_id: int) -> List[Balance]:
        return self.db.query(Balance).filter(Balance.group_id == group_id).all()

    def update_balance(self, user_id: int, owes_to_id: int, amount: float, currency_code: str = "USD", group_id: Optional[int] = None):
        """
        Updates the balances eagerly. If user_id owes owes_to_id `amount`, we first check if there is an existing reverse debt.
        If owes_to_id owes user_id $X, we reduce that X by `amount`. 
        If amount > X, we wipe out the reverse debt, and create/update a direct debt of (amount - X).
        """
        if user_id == owes_to_id or amount == 0:
            return  # Nobody owes themselves, and 0 means nothing happens

        amount_to_process = Decimal(str(amount))

        # Check for reverse debt: owes_to_id owes user_id
        reverse_q = self.db.query(Balance).filter(
            Balance.user_id == owes_to_id,
            Balance.owes_to_id == user_id,
            Balance.currency_code == currency_code
        )
        if group_id:
            reverse_q = reverse_q.filter(Balance.group_id == group_id)
        else:
            reverse_q = reverse_q.filter(Balance.group_id.is_(None))
            
        reverse_balance = reverse_q.first()

        if reverse_balance:
            reverse_amt = Decimal(str(reverse_balance.amount))
            if reverse_amt > amount_to_process:
                # Reverse debt reduces but stays positive
                reverse_balance.amount = float(reverse_amt - amount_to_process)
                self.db.commit()
                return
            elif reverse_amt == amount_to_process:
                # Cancel out completely
                self.db.delete(reverse_balance)
                self.db.commit()
                return
            else:
                # Reverse debt entirely consumed, some amount_to_process remains
                amount_to_process -= reverse_amt
                self.db.delete(reverse_balance)
                self.db.flush()

        # Check for direct debt: user_id owes owes_to_id
        direct_q = self.db.query(Balance).filter(
            Balance.user_id == user_id,
            Balance.owes_to_id == owes_to_id,
            Balance.currency_code == currency_code
        )
        if group_id:
            direct_q = direct_q.filter(Balance.group_id == group_id)
        else:
            direct_q = direct_q.filter(Balance.group_id.is_(None))
            
        direct_balance = direct_q.first()

        if direct_balance:
            # Increase direct debt
            direct_amt = Decimal(str(direct_balance.amount))
            direct_balance.amount = float(direct_amt + amount_to_process)
            self.db.commit()
        else:
            # Create new direct debt
            new_balance = Balance(
                user_id=user_id,
                owes_to_id=owes_to_id,
                amount=float(amount_to_process),
                currency_code=currency_code,
                group_id=group_id
            )
            self.db.add(new_balance)
            self.db.commit()
