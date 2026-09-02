from datetime import datetime, timezone

from app.models.transaction import Balance
from app.models.user import User
from app.repositories.transaction_repository import BalanceRepository


def test_balance_cache_round_trip_preserves_response_fields():
    now = datetime.now(timezone.utc)
    debtor = User(
        id=1,
        email="debtor@example.com",
        full_name="Debtor",
        hashed_password="not-cached",
        is_active=True,
        is_superuser=False,
        created_at=now,
        updated_at=now,
    )
    creditor = User(
        id=2,
        email="creditor@example.com",
        full_name="Creditor",
        hashed_password="not-cached",
        is_active=True,
        is_superuser=False,
        created_at=now,
        updated_at=now,
    )
    balance = Balance(
        id=3,
        user_id=debtor.id,
        owes_to_id=creditor.id,
        amount=12.50,
        currency_code="INR",
        group_id=4,
        last_updated=now,
        user=debtor,
        owes_to=creditor,
    )

    payload = BalanceRepository._serialize_balances([balance])
    restored = BalanceRepository._deserialize_balances(payload)

    assert restored[0].last_updated == now
    assert restored[0].user.email == debtor.email
    assert restored[0].owes_to.email == creditor.email
    assert "not-cached" not in payload
