import pytest
from pydantic import ValidationError

from app.schemas.expense import ExpenseSplitCreate
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
