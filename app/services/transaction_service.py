from typing import List
import logging

from app.repositories.transaction_repository import SettlementRepository, BalanceRepository
from app.repositories.user_repository import UserRepository
from app.repositories.group_repository import GroupRepository
from app.schemas.transaction import SettlementCreate, BalanceResponse
from app.models.transaction import Settlement
from app.models.user import User
from app.core.exceptions import BusinessLogicError, NotFoundError, ForbiddenError
from app.core.logging_config import LoggerMixin

class TransactionService(LoggerMixin):
    def __init__(
        self, 
        settlement_repo: SettlementRepository, 
        balance_repo: BalanceRepository, 
        user_repo: UserRepository,
        group_repo: GroupRepository
    ):
        self.settlement_repo = settlement_repo
        self.balance_repo = balance_repo
        self.user_repo = user_repo
        self.group_repo = group_repo

    def create_settlement(self, settlement_in: SettlementCreate, current_user: User) -> Settlement:
        self.logger.info(f"User {current_user.id} settling with {settlement_in.payee_id}")
        
        if settlement_in.payee_id == current_user.id:
            raise BusinessLogicError("Cannot settle with yourself")

        if settlement_in.group_id is not None:
            member = self.group_repo.get_member(settlement_in.group_id, current_user.id)
            if not member:
                raise ForbiddenError("Not a member of the specified group")

        payee = self.user_repo.get(settlement_in.payee_id)
        if not payee:
            raise NotFoundError("Payee not found")
        if settlement_in.group_id is not None:
            payee_member = self.group_repo.get_member(settlement_in.group_id, payee.id)
            if not payee_member:
                raise ForbiddenError("Payee is not a member of the specified group")

        try:
            settlement_data = settlement_in.model_dump()
            settlement = self.settlement_repo.create_settlement(settlement_data, current_user.id)

            self.balance_repo.update_balance(
                user_id=settlement.payee_id,
                owes_to_id=settlement.payer_id,
                amount=settlement.amount,
                currency_code=settlement.currency_code,
                group_id=settlement.group_id
            )
            settlement_id = settlement.id
            payee_id = settlement.payee_id
            payer_id = settlement.payer_id
            group_id = settlement.group_id
            self.settlement_repo.db.commit()
            self.balance_repo.invalidate_balance_cache(
                payee_id,
                payer_id,
                group_id,
            )
        except Exception as e:
            self.settlement_repo.db.rollback()
            self.logger.exception(f"Failed to create settlement: {str(e)}")
            raise BusinessLogicError("Failed to create settlement") from e

        self.logger.info(f"Settlement {settlement_id} created successfully")
        return settlement

    def get_group_balances(self, group_id: int, current_user: User) -> List[BalanceResponse]:
        member = self.group_repo.get_member(group_id, current_user.id)
        if not member:
            self.logger.warning(f"User {current_user.id} unauthorized access attempt to group {group_id} balances")
            raise ForbiddenError("Not a member of this group")
        return self.balance_repo.get_group_balances(group_id)

    def get_user_balances(self, current_user: User) -> List[BalanceResponse]:
        return self.balance_repo.get_user_balances(current_user.id)
