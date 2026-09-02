import pytest
from pydantic import ValidationError

from app.schemas.expense import ExpenseCreate, ExpenseSplitCreate
from app.schemas.transaction import SettlementCreate
from app.models.expense import SplitType
from app.schemas.user import UserCreate, UserUpdate


@pytest.mark.parametrize(
    ("field", "value"),
    [("amount", -1), ("percentage", -1), ("shares", -1)],
)
def test_expense_split_rejects_negative_values(field, value):
    with pytest.raises(ValidationError):
        ExpenseSplitCreate(user_id=1, **{field: value})


def test_user_create_requires_full_name():
    with pytest.raises(ValidationError):
        UserCreate(email="person@example.com", password="password123")


@pytest.mark.parametrize(
    "payload",
    [{"password": "short"}, {"password": None}, {"full_name": None}, {"email": None}],
)
def test_user_update_rejects_invalid_required_values(payload):
    with pytest.raises(ValidationError):
        UserUpdate(**payload)


def test_expense_rejects_non_inr_currency():
    with pytest.raises(ValidationError):
        ExpenseCreate(
            description="Dinner",
            amount=100,
            currency_code="USD",
            split_type=SplitType.EQUAL,
            splits=[ExpenseSplitCreate(user_id=1)],
        )


def test_expense_defaults_to_inr():
    expense = ExpenseCreate(
        description="Dinner",
        amount=100,
        split_type=SplitType.EQUAL,
        splits=[ExpenseSplitCreate(user_id=1)],
    )

    assert expense.currency_code == "INR"


def test_expense_rejects_sub_cent_amounts():
    with pytest.raises(ValidationError):
        ExpenseCreate(
            description="Dinner",
            amount="0.001",
            split_type=SplitType.EQUAL,
            splits=[ExpenseSplitCreate(user_id=1)],
        )


def test_settlement_rejects_non_inr_currency():
    with pytest.raises(ValidationError):
        SettlementCreate(payee_id=2, amount=50, currency_code="USD")


def test_settlement_defaults_to_inr():
    assert SettlementCreate(payee_id=2, amount=50).currency_code == "INR"


def test_settlement_rejects_sub_cent_amounts():
    with pytest.raises(ValidationError):
        SettlementCreate(payee_id=2, amount="0.001")
