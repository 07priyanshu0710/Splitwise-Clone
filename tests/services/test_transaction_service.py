import pytest
from unittest.mock import MagicMock
from types import SimpleNamespace
from app.services.transaction_service import TransactionService
from app.schemas.transaction import SettlementCreate
from app.core.exceptions import BusinessLogicError, ForbiddenError

@pytest.fixture
def mock_repos():
    return {
        "settlement_repo": MagicMock(),
        "balance_repo": MagicMock(),
        "user_repo": MagicMock(),
        "group_repo": MagicMock(),
        "audit_repo": MagicMock(),
    }

@pytest.fixture
def transaction_service(mock_repos):
    return TransactionService(
        settlement_repo=mock_repos["settlement_repo"],
        balance_repo=mock_repos["balance_repo"],
        user_repo=mock_repos["user_repo"],
        group_repo=mock_repos["group_repo"],
        audit_repo=mock_repos["audit_repo"],
    )

def test_create_settlement_self(transaction_service):
    current_user = MagicMock()
    current_user.id = 1
    settlement_in = SettlementCreate(payee_id=1, amount=50.0)
    
    with pytest.raises(BusinessLogicError) as exc:
        transaction_service.create_settlement(settlement_in, current_user)
    assert "Cannot settle with yourself" in str(exc.value)

def test_get_group_balances_unauthorized(transaction_service, mock_repos):
    current_user = MagicMock()
    current_user.id = 1
    group_id = 99
    mock_repos["group_repo"].get_member.return_value = None
    
    with pytest.raises(ForbiddenError) as exc:
        transaction_service.get_group_balances(group_id, current_user)
    assert "Not a member of this group" in str(exc.value)

def test_get_group_balances_success(transaction_service, mock_repos):
    current_user = MagicMock()
    current_user.id = 1
    group_id = 99
    mock_repos["group_repo"].get_member.return_value = MagicMock()
    mock_repos["balance_repo"].get_group_balances.return_value = []
    
    result = transaction_service.get_group_balances(group_id, current_user)
    
    assert result == []
    mock_repos["balance_repo"].get_group_balances.assert_called_once_with(group_id)


def test_create_settlement_rejects_non_member_payee(transaction_service, mock_repos):
    current_user = MagicMock(id=1)
    settlement_in = SettlementCreate(payee_id=2, amount=50.0, group_id=99)
    mock_repos["group_repo"].get_member.side_effect = [MagicMock(), None]
    mock_repos["user_repo"].get.return_value = SimpleNamespace(id=2)

    with pytest.raises(ForbiddenError, match="Payee"):
        transaction_service.create_settlement(settlement_in, current_user)


def test_create_settlement_rolls_back_when_balance_update_fails(transaction_service, mock_repos):
    current_user = MagicMock(id=1)
    settlement_in = SettlementCreate(payee_id=2, amount=50.0)
    mock_repos["user_repo"].get.return_value = SimpleNamespace(id=2)
    mock_repos["settlement_repo"].db = MagicMock()
    mock_repos["balance_repo"].get_outstanding_debt_for_update.return_value = SimpleNamespace(
        amount=50.0,
    )
    mock_repos["settlement_repo"].create_settlement.return_value = SimpleNamespace(
        id=5,
        payer_id=1,
        payee_id=2,
        amount=50.0,
        currency_code="INR",
        group_id=None,
    )
    mock_repos["balance_repo"].reduce_outstanding_debt.side_effect = RuntimeError("database failure")

    with pytest.raises(BusinessLogicError, match="Failed to create settlement"):
        transaction_service.create_settlement(settlement_in, current_user)

    mock_repos["settlement_repo"].db.rollback.assert_called_once_with()
    mock_repos["settlement_repo"].db.commit.assert_not_called()


def test_create_settlement_rejects_when_no_debt_exists(transaction_service, mock_repos):
    current_user = MagicMock(id=1)
    settlement_in = SettlementCreate(payee_id=2, amount=10.0)
    mock_repos["user_repo"].get.return_value = SimpleNamespace(id=2)
    mock_repos["settlement_repo"].db = MagicMock()
    mock_repos["balance_repo"].get_outstanding_debt_for_update.return_value = None

    with pytest.raises(BusinessLogicError, match="do not owe"):
        transaction_service.create_settlement(settlement_in, current_user)

    mock_repos["settlement_repo"].create_settlement.assert_not_called()
    mock_repos["settlement_repo"].db.rollback.assert_called_once_with()


def test_create_settlement_rejects_overpayment(transaction_service, mock_repos):
    current_user = MagicMock(id=1)
    settlement_in = SettlementCreate(payee_id=2, amount=50.01)
    mock_repos["user_repo"].get.return_value = SimpleNamespace(id=2)
    mock_repos["settlement_repo"].db = MagicMock()
    mock_repos["balance_repo"].get_outstanding_debt_for_update.return_value = SimpleNamespace(
        amount=50.0,
    )

    with pytest.raises(BusinessLogicError, match="exceeds"):
        transaction_service.create_settlement(settlement_in, current_user)

    mock_repos["settlement_repo"].create_settlement.assert_not_called()


def test_get_group_settlements_requires_membership(transaction_service, mock_repos):
    current_user = MagicMock(id=1)
    mock_repos["group_repo"].get_member.return_value = None

    with pytest.raises(ForbiddenError, match="Not a member"):
        transaction_service.get_group_settlements(99, current_user)
