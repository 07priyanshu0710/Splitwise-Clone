from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, text
from typing import List, Optional
from decimal import Decimal
import json
import logging

logger = logging.getLogger(__name__)

from app.repositories.base import BaseRepository
from app.models.transaction import Settlement, Balance
from app.core.redis import redis_client
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
        cache_key = f"user_balances:{user_id}"
        if redis_client:
            try:
                cached = redis_client.get(cache_key)
                if cached:
                    logger.info(f"Redis cache hit for user_balances:{user_id}")
                    return self._deserialize_balances(cached)
            except Exception as e:
                logger.warning(f"Redis error in get_user_balances: {e}")

        logger.info(f"Redis cache miss/bypass for user_balances:{user_id}. Fetching from DB.")
        balances = self.db.query(Balance).options(
            joinedload(Balance.user),
            joinedload(Balance.owes_to)
        ).filter(
            or_(Balance.user_id == user_id, Balance.owes_to_id == user_id)
        ).all()
        
        responses = [BalanceResponse.model_validate(balance) for balance in balances]
        if redis_client:
            try:
                redis_client.set(cache_key, self._serialize_balances(responses), ex=3600)
            except Exception as e:
                logger.warning(f"Redis error during caching: {e}")
        
        return responses

    def get_group_balances(self, group_id: int) -> List[BalanceResponse]:
        cache_key = f"group_balances:{group_id}"
        if redis_client:
            try:
                cached = redis_client.get(cache_key)
                if cached:
                    return self._deserialize_balances(cached)
            except Exception as e:
                logger.warning(f"Redis error in get_group_balances: {e}")
            
        balances = self.db.query(Balance).options(
            joinedload(Balance.user),
            joinedload(Balance.owes_to)
        ).filter(Balance.group_id == group_id).all()
        
        responses = [BalanceResponse.model_validate(balance) for balance in balances]
        if redis_client:
            try:
                redis_client.set(cache_key, self._serialize_balances(responses), ex=3600)
            except Exception as e:
                logger.warning(f"Redis error during caching: {e}")
                
        return responses

    @staticmethod
    def _serialize_balances(balances: List[Balance | BalanceResponse]) -> str:
        payload = [
            BalanceResponse.model_validate(balance).model_dump(mode="json")
            for balance in balances
        ]
        return json.dumps(payload)

    @staticmethod
    def _deserialize_balances(payload: str) -> List[BalanceResponse]:
        return [BalanceResponse.model_validate(item) for item in json.loads(payload)]

    def invalidate_balance_cache(self, user_id: int, owes_to_id: int, group_id: Optional[int] = None):
        if redis_client:
            try:
                logger.info(f"Invalidating Redis cache: user:{user_id}, owes:{owes_to_id}, group:{group_id}")
                redis_client.delete(f"user_balances:{user_id}")
                redis_client.delete(f"user_balances:{owes_to_id}")
                if group_id is not None:
                    redis_client.delete(f"group_balances:{group_id}")
            except Exception as e:
                logger.warning(f"Redis invalidation failed: {e}")

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
                reverse_balance.amount = float(reverse_amt - amount_to_process)
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
            direct_balance.amount = float(direct_amt + amount_to_process)
        else:
            new_balance = Balance(
                user_id=user_id,
                owes_to_id=owes_to_id,
                amount=float(amount_to_process),
                currency_code=INR_CURRENCY_CODE,
                group_id=group_id
            )
            self.db.add(new_balance)
