from decimal import Decimal
from unittest.mock import MagicMock

from app.models.transaction import Balance
from app.repositories.transaction_repository import BalanceRepository


def test_reduce_outstanding_debt_updates_partial_balance():
    db = MagicMock()
    balance = Balance(amount=Decimal("50.00"))

    BalanceRepository(db).reduce_outstanding_debt(balance, Decimal("20.00"))

    assert balance.amount == Decimal("30.00")
    db.delete.assert_not_called()
    db.flush.assert_called_once_with()


def test_reduce_outstanding_debt_deletes_fully_paid_balance():
    db = MagicMock()
    balance = Balance(amount=Decimal("50.00"))

    BalanceRepository(db).reduce_outstanding_debt(balance, Decimal("50.00"))

    db.delete.assert_called_once_with(balance)
    db.flush.assert_called_once_with()
