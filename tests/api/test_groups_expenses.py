import pytest
from app.models.group import Group
from app.models.expense import Expense, SplitType

import pytest

def test_groups_and_expenses_flow(client, test_user_token_headers):
    # 1. Create Group
    response = client.post(
        "/api/v1/groups/",
        headers=test_user_token_headers["token1"],
        json={"name": "Test Group"}
    )
    assert response.status_code == 200
    data = response.json()
    group_id = data["id"]
    
    # 2. Add member
    email2 = test_user_token_headers["email2"]
    response = client.post(
        f"/api/v1/groups/{group_id}/members",
        headers=test_user_token_headers["token1"],
        json={"identifier": email2}
    )
    assert response.status_code == 200
    assert len(response.json()["members"]) == 2

    # 3. Create Expense Equal
    uid1 = test_user_token_headers["user1_id"]
    uid2 = test_user_token_headers["user2_id"]

    expense_data = {
        "description": "Lunch",
        "amount": 100.0,
        "group_id": group_id,
        "split_type": "equal",
        "splits": [{"user_id": uid1}, {"user_id": uid2}]
    }
    response = client.post(
        "/api/v1/expenses/",
        headers=test_user_token_headers["token1"],
        json=expense_data
    )
    assert response.status_code == 200
    assert response.json()["amount"] == 100.0

    # 4. Check Balances
    response = client.get(
        "/api/v1/balances/me",
        headers=test_user_token_headers["token1"]
    )
    assert response.status_code == 200
    balances = response.json()
    assert len(balances) > 0
    owed = balances[0]
    assert owed["user_id"] == uid2
    assert owed["owes_to_id"] == uid1
    assert owed["amount"] == 50.0

    # The second read is served from Redis when it is available. Its shape must
    # remain identical to the database-backed response.
    cached_response = client.get(
        "/api/v1/balances/me",
        headers=test_user_token_headers["token1"]
    )
    assert cached_response.status_code == 200
    assert cached_response.json()[0]["last_updated"]
    assert cached_response.json()[0]["user"]["id"] == uid2

    # 5. Settlement
    settlement_data = {
        "payee_id": uid1,
        "amount": 50.0,
        "group_id": group_id,
        "description": "Pay back for Lunch"
    }
    response = client.post(
        "/api/v1/settlements/",
        headers=test_user_token_headers["token2"],
        json=settlement_data
    )
    assert response.status_code == 200

    # 6. Verify balances zeroed out
    response = client.get(
        "/api/v1/balances/me",
        headers=test_user_token_headers["token1"]
    )
    assert len(response.json()) == 0
