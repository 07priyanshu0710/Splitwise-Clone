from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List

from app.repositories.transaction_repository import SettlementRepository, BalanceRepository
from app.repositories.user_repository import UserRepository
from app.schemas.transaction import SettlementCreate
from app.models.transaction import Settlement, Balance
from app.models.user import User

class TransactionService:
    def __init__(self, db: Session):
        self.db = db
        self.settlement_repo = SettlementRepository(db)
        self.balance_repo = BalanceRepository(db)
        self.user_repo = UserRepository(db)

    def create_settlement(self, settlement_in: SettlementCreate, current_user: User) -> Settlement:
        if settlement_in.payee_id == current_user.id:
            raise HTTPException(status_code=400, detail="Cannot settle with yourself")

        payee = self.user_repo.get(settlement_in.payee_id)
        if not payee:
            raise HTTPException(status_code=404, detail="Payee not found")

        settlement_data = settlement_in.model_dump()
        settlement = self.settlement_repo.create_settlement(settlement_data, current_user.id)

        self.balance_repo.update_balance(
            user_id=settlement.payee_id,
            owes_to_id=settlement.payer_id,
            amount=settlement.amount,
            currency_code=settlement.currency_code,
            group_id=settlement.group_id
        )

        return settlement

    def get_group_balances(self, group_id: int, current_user: User) -> List[Balance]:
        return self.balance_repo.get_group_balances(group_id)

    def get_user_balances(self, current_user: User) -> List[Balance]:
        return self.balance_repo.get_user_balances(current_user.id)
