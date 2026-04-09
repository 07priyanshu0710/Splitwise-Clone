from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from typing import List, Optional
from decimal import Decimal
import json
import logging

logger = logging.getLogger(__name__)

from app.repositories.base import BaseRepository
from app.models.transaction import Settlement, Balance
from app.core.redis import redis_client

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
        cache_key = f"user_balances:{user_id}"
        if redis_client:
            try:
                cached = redis_client.get(cache_key)
                if cached:
                    logger.info(f"Redis cache hit for user_balances:{user_id}")
                    data = json.loads(cached)
                    return [Balance(**b) for b in data]
            except Exception as e:
                logger.warning(f"Redis error in get_user_balances: {e}")

        logger.info(f"Redis cache miss/bypass for user_balances:{user_id}. Fetching from DB.")
        balances = self.db.query(Balance).options(
            joinedload(Balance.user),
            joinedload(Balance.owes_to)
        ).filter(
            or_(Balance.user_id == user_id, Balance.owes_to_id == user_id)
        ).all()
        
        if redis_client:
            try:
                cache_data = [
                    {
                        "id": b.id, "user_id": b.user_id, "owes_to_id": b.owes_to_id,
                        "amount": float(b.amount), "currency_code": b.currency_code,
                        "group_id": b.group_id
                    } for b in balances
                ]
                redis_client.setex(cache_key, 3600, json.dumps(cache_data))
            except Exception as e:
                logger.warning(f"Redis error during caching: {e}")
        
        return balances

    def get_group_balances(self, group_id: int) -> List[Balance]:
        cache_key = f"group_balances:{group_id}"
        if redis_client:
            try:
                cached = redis_client.get(cache_key)
                if cached:
                    data = json.loads(cached)
                    return [Balance(**b) for b in data]
            except Exception as e:
                logger.warning(f"Redis error in get_group_balances: {e}")
            
        balances = self.db.query(Balance).filter(Balance.group_id == group_id).all()
        
        if redis_client:
            try:
                cache_data = [
                    {
                        "id": b.id, "user_id": b.user_id, "owes_to_id": b.owes_to_id,
                        "amount": float(b.amount), "currency_code": b.currency_code,
                        "group_id": b.group_id
                    } for b in balances
                ]
                redis_client.setex(cache_key, 3600, json.dumps(cache_data))
            except Exception as e:
                logger.warning(f"Redis error during caching: {e}")
                
        return balances

    def _invalidate_balance_cache(self, user_id: int, owes_to_id: int, group_id: Optional[int] = None):
        if redis_client:
            try:
                logger.info(f"Invalidating Redis cache: user:{user_id}, owes:{owes_to_id}, group:{group_id}")
                redis_client.delete(f"user_balances:{user_id}")
                redis_client.delete(f"user_balances:{owes_to_id}")
                if group_id:
                    redis_client.delete(f"group_balances:{group_id}")
            except Exception as e:
                logger.warning(f"Redis invalidation failed: {e}")

    def update_balance(self, user_id: int, owes_to_id: int, amount: float, currency_code: str = "USD", group_id: Optional[int] = None):
        if user_id == owes_to_id or amount == 0:
            return

        amount_to_process = Decimal(str(amount))

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
                reverse_balance.amount = float(reverse_amt - amount_to_process)
            elif reverse_amt == amount_to_process:
                self.db.delete(reverse_balance)
            else:
                amount_to_process -= reverse_amt
                self.db.delete(reverse_balance)
                self.db.flush()
                self._update_direct_balance(user_id, owes_to_id, amount_to_process, currency_code, group_id)
        else:
            self._update_direct_balance(user_id, owes_to_id, amount_to_process, currency_code, group_id)
        
        self.db.commit()
        self._invalidate_balance_cache(user_id, owes_to_id, group_id)

    def _update_direct_balance(self, user_id, owes_to_id, amount_to_process, currency_code, group_id):
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
            direct_amt = Decimal(str(direct_balance.amount))
            direct_balance.amount = float(direct_amt + amount_to_process)
        else:
            new_balance = Balance(
                user_id=user_id,
                owes_to_id=owes_to_id,
                amount=float(amount_to_process),
                currency_code=currency_code,
                group_id=group_id
            )
            self.db.add(new_balance)
