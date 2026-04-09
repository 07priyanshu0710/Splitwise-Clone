import pytest
from unittest.mock import MagicMock
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
        "balance_repo": MagicMock()
    }

@pytest.fixture
def expense_service(mock_repos):
    return ExpenseService(
        repository=mock_repos["expense_repo"],
        group_repository=mock_repos["group_repo"],
        balance_repository=mock_repos["balance_repo"]
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
    assert splits[0].amount == 33.34
    assert splits[1].amount == 33.33
    assert splits[2].amount == 33.33
    assert sum(s.amount for s in splits) == 100.00

def test_validate_percentage_split_success(expense_service):
    total = Decimal("200.00")
    splits = [
        ExpenseSplitCreate(user_id=1, percentage=50.0),
        ExpenseSplitCreate(user_id=2, percentage=50.0)
    ]
    
    expense_service._validate_percentage_split(total, splits)
    
    assert splits[0].amount == 100.00
    assert splits[1].amount == 100.00

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
        curvature_code="USD",
        split_type=SplitType.EQUAL,
        group_id=1,
        splits=[ExpenseSplitCreate(user_id=1)]
    )
    current_user = MagicMock()
    current_user.id = 1
    
    with pytest.raises(ForbiddenError):
        expense_service.create_expense(expense_in, current_user)
