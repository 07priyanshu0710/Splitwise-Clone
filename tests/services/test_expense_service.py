import pytest
from unittest.mock import MagicMock
from types import SimpleNamespace
from decimal import Decimal
from app.services.expense_service import ExpenseService
from app.schemas.expense import ExpenseCreate, ExpenseSplitCreate
from app.models.expense import SplitType
from app.core.exceptions import BusinessLogicError, ForbiddenError

@pytest.fixture
def mock_repos():
    return {
        "expense_repo": MagicMock(),
        "group_repo": MagicMock(),
        "balance_repo": MagicMock(),
        "audit_repo": MagicMock(),
    }

@pytest.fixture
def expense_service(mock_repos):
    return ExpenseService(
        repository=mock_repos["expense_repo"],
        group_repository=mock_repos["group_repo"],
        balance_repository=mock_repos["balance_repo"],
        audit_repository=mock_repos["audit_repo"],
    )

def test_validate_equal_split(expense_service):
    total = Decimal("100.00")
    splits = [
        ExpenseSplitCreate(user_id=1),
        ExpenseSplitCreate(user_id=2),
        ExpenseSplitCreate(user_id=3)
    ]
    
    expense_service._validate_equal_split(total, splits)
    
    # 100 / 3 = 33.33. First one gets the remainder.
    # 33.33 * 3 = 99.99. Remainder = 0.01.
    # splits[0] = 33.33 + 0.01 = 33.34
    assert splits[0].amount == Decimal("33.34")
    assert splits[1].amount == Decimal("33.33")
    assert splits[2].amount == Decimal("33.33")
    assert sum(s.amount for s in splits) == Decimal("100.00")

def test_validate_percentage_split_success(expense_service):
    total = Decimal("200.00")
    splits = [
        ExpenseSplitCreate(user_id=1, percentage=50.0),
        ExpenseSplitCreate(user_id=2, percentage=50.0)
    ]
    
    expense_service._validate_percentage_split(total, splits)
    
    assert splits[0].amount == Decimal("100.00")
    assert splits[1].amount == Decimal("100.00")

def test_validate_percentage_split_invalid_sum(expense_service):
    total = Decimal("200.00")
    splits = [
        ExpenseSplitCreate(user_id=1, percentage=50.0),
        ExpenseSplitCreate(user_id=2, percentage=40.0)
    ]
    
    with pytest.raises(BusinessLogicError) as excinfo:
        expense_service._validate_percentage_split(total, splits)
    assert "Sum of percentages" in str(excinfo.value)

def test_create_expense_forbidden_group(expense_service, mock_repos):
    mock_repos["group_repo"].get_member.return_value = None
    
    expense_in = ExpenseCreate(
        description="Dinner",
        amount=100.00,
        currency_code="INR",
        split_type=SplitType.EQUAL,
        group_id=1,
        splits=[ExpenseSplitCreate(user_id=1)]
    )
    current_user = MagicMock()
    current_user.id = 1
    
    with pytest.raises(ForbiddenError):
        expense_service.create_expense(expense_in, current_user)


def test_create_expense_rejects_non_group_participant(expense_service, mock_repos):
    mock_repos["group_repo"].get_member.return_value = MagicMock()
    mock_repos["group_repo"].get_member_user_ids.return_value = {1}
    expense_in = ExpenseCreate(
        description="Dinner",
        amount=100.00,
        split_type=SplitType.EQUAL,
        group_id=1,
        splits=[ExpenseSplitCreate(user_id=1), ExpenseSplitCreate(user_id=2)]
    )
    current_user = MagicMock(id=1)

    with pytest.raises(ForbiddenError, match="participants"):
        expense_service.create_expense(expense_in, current_user)


def test_create_expense_rolls_back_when_balance_update_fails(expense_service, mock_repos):
    mock_repos["expense_repo"].db = MagicMock()
    mock_repos["expense_repo"].create_with_splits.return_value = SimpleNamespace(
        id=7,
        payer_id=1,
        group_id=None,
        currency_code="INR",
        splits=[SimpleNamespace(user_id=2, amount=50.0)],
    )
    mock_repos["balance_repo"].update_balance.side_effect = RuntimeError("database failure")
    expense_in = ExpenseCreate(
        description="Dinner",
        amount=100.00,
        split_type=SplitType.EQUAL,
        splits=[ExpenseSplitCreate(user_id=1), ExpenseSplitCreate(user_id=2)]
    )
    current_user = MagicMock(id=1)

    with pytest.raises(BusinessLogicError, match="Failed to create expense"):
        expense_service.create_expense(expense_in, current_user)

    mock_repos["expense_repo"].db.rollback.assert_called_once_with()
    mock_repos["expense_repo"].db.commit.assert_not_called()
