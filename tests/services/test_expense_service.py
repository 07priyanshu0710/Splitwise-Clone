import pytest
from app.services.expense_service import ExpenseService
from app.models.expense import SplitType
from decimal import Decimal
from typing import List
from pydantic import BaseModel
from fastapi import HTTPException

# Mocking Split object since we need .amount property access
class MockSplit:
    def __init__(self, amount=None, percentage=None, shares=None):
        self.amount = amount
        self.percentage = percentage
        self.shares = shares

class MockExpenseService(ExpenseService):
    def __init__(self):
        # Do not initialize db repositories
        pass

def test_equal_split():
    svc = MockExpenseService()
    splits = [MockSplit(), MockSplit(), MockSplit()]
    svc._validate_equal_split(Decimal('100.00'), splits)
    # Expected: 33.34, 33.33, 33.33
    assert splits[0].amount == 33.34
    assert splits[1].amount == 33.33
    assert splits[2].amount == 33.33

def test_percentage_split():
    svc = MockExpenseService()
    splits = [MockSplit(percentage=60), MockSplit(percentage=40)]
    svc._validate_percentage_split(Decimal('200.00'), splits)
    assert splits[0].amount == 120.0
    assert splits[1].amount == 80.0

def test_percentage_split_invalid_sum():
    svc = MockExpenseService()
    splits = [MockSplit(percentage=50), MockSplit(percentage=40)]
    with pytest.raises(HTTPException) as excinfo:
        svc._validate_percentage_split(Decimal('200.00'), splits)
    assert excinfo.value.status_code == 400

def test_share_split():
    svc = MockExpenseService()
    splits = [MockSplit(shares=2), MockSplit(shares=1)]
    svc._validate_share_split(Decimal('90.00'), splits)
    assert splits[0].amount == 60.0 # 2/3 of 90
    assert splits[1].amount == 30.0 # 1/3 of 90

def test_unequal_split():
    svc = MockExpenseService()
    splits = [MockSplit(amount=70.0), MockSplit(amount=30.0)]
    svc._validate_unequal_split(Decimal('100.00'), splits)
    
def test_unequal_split_invalid():
    svc = MockExpenseService()
    splits = [MockSplit(amount=70.0), MockSplit(amount=40.0)]
    with pytest.raises(HTTPException) as excinfo:
        svc._validate_unequal_split(Decimal('100.00'), splits)
    assert excinfo.value.status_code == 400
