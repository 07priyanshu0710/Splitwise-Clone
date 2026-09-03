import pytest
from unittest.mock import MagicMock
from types import SimpleNamespace
from decimal import Decimal
from app.services.expense_service import ExpenseService
from app.schemas.expense import ExpenseCreate, ExpenseSplitCreate
from app.models.expense import SplitType
from app.core.exceptions import BusinessLogicError, ForbiddenError, NotFoundError

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


def test_validate_unequal_split_success(expense_service):
    total = Decimal("150.00")
    splits = [
        ExpenseSplitCreate(user_id=1, amount=Decimal("100.00")),
        ExpenseSplitCreate(user_id=2, amount=Decimal("50.00")),
    ]
    expense_service._validate_unequal_split(total, splits)
    assert splits[0].amount == Decimal("100.00")
    assert splits[1].amount == Decimal("50.00")
    assert splits[0].percentage is None
    assert splits[0].shares is None


def test_validate_unequal_split_missing_amount(expense_service):
    total = Decimal("150.00")
    splits = [
        ExpenseSplitCreate(user_id=1, amount=None),
        ExpenseSplitCreate(user_id=2, amount=Decimal("50.00")),
    ]
    with pytest.raises(BusinessLogicError, match="Amount must be provided"):
        expense_service._validate_unequal_split(total, splits)


def test_validate_unequal_split_sum_mismatch(expense_service):
    total = Decimal("150.00")
    splits = [
        ExpenseSplitCreate(user_id=1, amount=Decimal("100.00")),
        ExpenseSplitCreate(user_id=2, amount=Decimal("40.00")),
    ]
    with pytest.raises(BusinessLogicError, match="does not equal total amount"):
        expense_service._validate_unequal_split(total, splits)


def test_validate_share_split_success(expense_service):
    total = Decimal("100.00")
    splits = [
        ExpenseSplitCreate(user_id=1, shares=Decimal("1")),
        ExpenseSplitCreate(user_id=2, shares=Decimal("2")),
    ]
    expense_service._validate_share_split(total, splits)
    # 100 * 1 / 3 = 33.33, 100 * 2 / 3 = 66.67. Remainder = 0.00.
    assert sum(s.amount for s in splits) == Decimal("100.00")
    assert splits[0].amount == Decimal("33.33")
    assert splits[1].amount == Decimal("66.67")


def test_validate_share_split_with_remainder(expense_service):
    total = Decimal("100.00")
    splits = [
        ExpenseSplitCreate(user_id=1, shares=Decimal("1")),
        ExpenseSplitCreate(user_id=2, shares=Decimal("1")),
        ExpenseSplitCreate(user_id=3, shares=Decimal("1")),
    ]
    expense_service._validate_share_split(total, splits)
    # 100 / 3 = 33.33 * 3 = 99.99, remainder 0.01 added to first split
    assert splits[0].amount == Decimal("33.34")
    assert splits[1].amount == Decimal("33.33")
    assert splits[2].amount == Decimal("33.33")
    assert sum(s.amount for s in splits) == Decimal("100.00")


def test_validate_share_split_missing_shares(expense_service):
    total = Decimal("100.00")
    splits = [
        ExpenseSplitCreate(user_id=1, shares=None),
        ExpenseSplitCreate(user_id=2, shares=Decimal("2")),
    ]
    with pytest.raises(BusinessLogicError, match="Shares must be provided"):
        expense_service._validate_share_split(total, splits)


def test_validate_share_split_zero_shares(expense_service):
    total = Decimal("100.00")
    splits = [
        ExpenseSplitCreate(user_id=1, shares=Decimal("0")),
        ExpenseSplitCreate(user_id=2, shares=Decimal("0")),
    ]
    with pytest.raises(BusinessLogicError, match="greater than zero"):
        expense_service._validate_share_split(total, splits)


def test_create_expense_rejects_duplicate_user_splits(expense_service):
    expense_in = ExpenseCreate(
        description="Dinner",
        amount=100.00,
        split_type=SplitType.EQUAL,
        splits=[ExpenseSplitCreate(user_id=1), ExpenseSplitCreate(user_id=1)],
    )
    current_user = MagicMock(id=1)
    with pytest.raises(BusinessLogicError, match="appear only once"):
        expense_service.create_expense(expense_in, current_user)


def test_get_expense_not_found(expense_service, mock_repos):
    mock_repos["expense_repo"].get_with_details.return_value = None
    with pytest.raises(NotFoundError, match="Expense not found"):
        expense_service.get_expense(999, user_id=1)


def test_get_expense_forbidden(expense_service, mock_repos):
    mock_repos["expense_repo"].get_with_details.return_value = SimpleNamespace(
        id=5,
        payer_id=2,
        splits=[SimpleNamespace(user_id=3)],
    )
    with pytest.raises(ForbiddenError, match="do not have access"):
        expense_service.get_expense(5, user_id=1)


def test_get_group_expenses_forbidden(expense_service, mock_repos):
    mock_repos["group_repo"].get_member.return_value = None
    with pytest.raises(ForbiddenError, match="Not a member"):
        expense_service.get_group_expenses(99, user_id=1)
