import pytest
from unittest.mock import MagicMock
from app.services.transaction_service import TransactionService
from app.schemas.transaction import SettlementCreate
from app.core.exceptions import BusinessLogicError, ForbiddenError

@pytest.fixture
def mock_repos():
    return {
        "settlement_repo": MagicMock(),
        "balance_repo": MagicMock(),
        "user_repo": MagicMock(),
        "group_repo": MagicMock()
    }

@pytest.fixture
def transaction_service(mock_repos):
    return TransactionService(
        settlement_repo=mock_repos["settlement_repo"],
        balance_repo=mock_repos["balance_repo"],
        user_repo=mock_repos["user_repo"],
        group_repo=mock_repos["group_repo"]
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
