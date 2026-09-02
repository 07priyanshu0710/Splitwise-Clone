from decimal import Decimal
from typing import List

from app.repositories.transaction_repository import SettlementRepository, BalanceRepository
from app.repositories.user_repository import UserRepository
from app.repositories.group_repository import GroupRepository
from app.repositories.audit_repository import AuditRepository
from app.schemas.transaction import SettlementCreate, BalanceResponse
from app.models.transaction import Settlement
from app.models.user import User
from app.core.exceptions import BusinessLogicError, NotFoundError, ForbiddenError
from app.core.constants import INR_CURRENCY_CODE
from app.core.logging_config import LoggerMixin

class TransactionService(LoggerMixin):
    def __init__(
        self, 
        settlement_repo: SettlementRepository, 
        balance_repo: BalanceRepository, 
        user_repo: UserRepository,
        group_repo: GroupRepository,
        audit_repo: AuditRepository,
    ):
        self.settlement_repo = settlement_repo
        self.balance_repo = balance_repo
        self.user_repo = user_repo
        self.group_repo = group_repo
        self.audit_repo = audit_repo

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
            outstanding_debt = self.balance_repo.get_outstanding_debt_for_update(
                debtor_id=current_user.id,
                creditor_id=payee.id,
                group_id=settlement_in.group_id,
            )
            if outstanding_debt is None:
                raise BusinessLogicError("You do not owe this user in the specified group")

            settlement_amount = Decimal(str(settlement_in.amount))
            outstanding_amount = Decimal(str(outstanding_debt.amount))
            if settlement_amount > outstanding_amount:
                raise BusinessLogicError(
                    f"Settlement amount exceeds the outstanding debt of {INR_CURRENCY_CODE} {outstanding_amount:.2f}"
                )

            settlement_data = settlement_in.model_dump()
            settlement = self.settlement_repo.create_settlement(settlement_data, current_user.id)

            self.balance_repo.reduce_outstanding_debt(
                outstanding_debt,
                settlement_amount,
            )
            self.audit_repo.record(
                action="settlement.created",
                entity_type="settlement",
                entity_id=settlement.id,
                user_id=current_user.id,
                changes={
                    "group_id": settlement.group_id,
                    "payer_id": settlement.payer_id,
                    "payee_id": settlement.payee_id,
                    "amount": f"{settlement_amount:.2f}",
                    "currency_code": INR_CURRENCY_CODE,
                    "outstanding_before": f"{outstanding_amount:.2f}",
                    "outstanding_after": f"{outstanding_amount - settlement_amount:.2f}",
                },
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
        except BusinessLogicError:
            self.settlement_repo.db.rollback()
            raise
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

    def get_group_settlements(self, group_id: int, current_user: User) -> List[Settlement]:
        member = self.group_repo.get_member(group_id, current_user.id)
        if not member:
            raise ForbiddenError("Not a member of this group")
        return self.settlement_repo.get_group_settlements(group_id)

    def get_user_balances(self, current_user: User) -> List[BalanceResponse]:
        return self.balance_repo.get_user_balances(current_user.id)
