from app.models.audit import AuditLog
from app.models.transaction import Balance


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
    assert response.json()["currency_code"] == "INR"

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
    assert owed["currency_code"] == "INR"

    # Repeated reads must preserve the complete response shape.
    repeated_response = client.get(
        "/api/v1/balances/me",
        headers=test_user_token_headers["token1"]
    )
    assert repeated_response.status_code == 200
    assert repeated_response.json()[0]["last_updated"]
    assert repeated_response.json()[0]["user"]["id"] == uid2

    # 5. Settlement
    settlement_data = {
        "payee_id": uid1,
        "amount": 50.0,
        "group_id": group_id,
        "description": "Pay back for Lunch"
    }
    overpayment_response = client.post(
        "/api/v1/settlements/",
        headers=test_user_token_headers["token2"],
        json={**settlement_data, "amount": 50.01},
    )
    assert overpayment_response.status_code == 400
    assert "exceeds" in overpayment_response.json()["detail"]

    response = client.post(
        "/api/v1/settlements/",
        headers=test_user_token_headers["token2"],
        json=settlement_data
    )
    assert response.status_code == 200

    history_response = client.get(
        f"/api/v1/settlements/group/{group_id}",
        headers=test_user_token_headers["token1"],
    )
    assert history_response.status_code == 200
    assert len(history_response.json()) == 1
    assert history_response.json()[0]["payer_id"] == uid2
    assert history_response.json()[0]["payee_id"] == uid1
    assert history_response.json()[0]["currency_code"] == "INR"

    # 6. Verify balances zeroed out
    response = client.get(
        "/api/v1/balances/me",
        headers=test_user_token_headers["token1"]
    )
    assert len(response.json()) == 0


def test_financial_mutations_create_audit_logs(client, db, test_user_token_headers):
    response = client.post(
        "/api/v1/groups/",
        headers=test_user_token_headers["token1"],
        json={"name": "Audited Group"},
    )
    group_id = response.json()["id"]
    client.post(
        f"/api/v1/groups/{group_id}/members",
        headers=test_user_token_headers["token1"],
        json={"identifier": test_user_token_headers["email2"]},
    )
    uid1 = test_user_token_headers["user1_id"]
    uid2 = test_user_token_headers["user2_id"]
    client.post(
        "/api/v1/expenses/",
        headers=test_user_token_headers["token1"],
        json={
            "description": "Dinner",
            "amount": 100,
            "group_id": group_id,
            "split_type": "equal",
            "splits": [{"user_id": uid1}, {"user_id": uid2}],
        },
    )
    client.post(
        "/api/v1/settlements/",
        headers=test_user_token_headers["token2"],
        json={"payee_id": uid1, "amount": 25, "group_id": group_id},
    )

    remaining_balance = db.query(Balance).filter(
        Balance.user_id == uid2,
        Balance.owes_to_id == uid1,
        Balance.group_id == group_id,
    ).one()
    assert float(remaining_balance.amount) == 25.0

    logs = db.query(AuditLog).order_by(AuditLog.id).all()
    assert [log.action for log in logs] == ["expense.created", "settlement.created"]
    assert logs[0].changes["currency_code"] == "INR"
    assert logs[1].changes["outstanding_after"] == "25.00"


def test_opposite_expenses_net_toward_the_larger_payer(client, test_user_token_headers):
    response = client.post(
        "/api/v1/groups/",
        headers=test_user_token_headers["token1"],
        json={"name": "Two Payers"},
    )
    assert response.status_code == 200
    group_id = response.json()["id"]

    response = client.post(
        f"/api/v1/groups/{group_id}/members",
        headers=test_user_token_headers["token1"],
        json={"identifier": test_user_token_headers["email2"]},
    )
    assert response.status_code == 200

    user1_id = test_user_token_headers["user1_id"]
    user2_id = test_user_token_headers["user2_id"]
    splits = [{"user_id": user1_id}, {"user_id": user2_id}]

    response = client.post(
        "/api/v1/expenses/",
        headers=test_user_token_headers["token1"],
        json={
            "description": "Food",
            "amount": 200.0,
            "group_id": group_id,
            "split_type": "equal",
            "splits": splits,
        },
    )
    assert response.status_code == 200

    response = client.post(
        "/api/v1/expenses/",
        headers=test_user_token_headers["token2"],
        json={
            "description": "Taxi",
            "amount": 100.0,
            "group_id": group_id,
            "split_type": "equal",
            "splits": splits,
        },
    )
    assert response.status_code == 200

    user1_balances = client.get(
        "/api/v1/balances/me",
        headers=test_user_token_headers["token1"],
    )
    user2_balances = client.get(
        "/api/v1/balances/me",
        headers=test_user_token_headers["token2"],
    )

    assert user1_balances.status_code == 200
    assert user2_balances.status_code == 200
    assert user1_balances.json() == user2_balances.json()
    assert len(user1_balances.json()) == 1
    assert user1_balances.json()[0]["user_id"] == user2_id
    assert user1_balances.json()[0]["owes_to_id"] == user1_id
    assert user1_balances.json()[0]["amount"] == 50.0


def test_unequal_and_share_split_integration(client, test_user_token_headers):
    # 1. Create Group
    response = client.post(
        "/api/v1/groups/",
        headers=test_user_token_headers["token1"],
        json={"name": "Multi-Split Group"},
    )
    assert response.status_code == 200
    group_id = response.json()["id"]

    # 2. Add member
    client.post(
        f"/api/v1/groups/{group_id}/members",
        headers=test_user_token_headers["token1"],
        json={"identifier": test_user_token_headers["email2"]},
    )

    user1_id = test_user_token_headers["user1_id"]
    user2_id = test_user_token_headers["user2_id"]

    # 3. Create Unequal split expense: 100 total (User1: 60, User2: 40)
    unequal_resp = client.post(
        "/api/v1/expenses/",
        headers=test_user_token_headers["token1"],
        json={
            "description": "Groceries",
            "amount": 100.0,
            "group_id": group_id,
            "split_type": "unequal",
            "splits": [
                {"user_id": user1_id, "amount": 60.0},
                {"user_id": user2_id, "amount": 40.0},
            ],
        },
    )
    assert unequal_resp.status_code == 200
    expense_id = unequal_resp.json()["id"]

    # Verify single expense retrieval
    get_resp = client.get(
        f"/api/v1/expenses/{expense_id}",
        headers=test_user_token_headers["token1"],
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["split_type"] == "unequal"

    # 4. Create Share split expense: 200 total (User1: 1 share, User2: 3 shares)
    share_resp = client.post(
        "/api/v1/expenses/",
        headers=test_user_token_headers["token1"],
        json={
            "description": "Hotel",
            "amount": 200.0,
            "group_id": group_id,
            "split_type": "share",
            "splits": [
                {"user_id": user1_id, "shares": 1.0},
                {"user_id": user2_id, "shares": 3.0},
            ],
        },
    )
    assert share_resp.status_code == 200
    assert share_resp.json()["split_type"] == "share"

    # 5. Verify group expenses list endpoint
    list_resp = client.get(
        f"/api/v1/expenses/group/{group_id}",
        headers=test_user_token_headers["token1"],
    )
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 2

    # 6. Verify total balances: User2 owes 40 + 150 = 190
    bal_resp = client.get(
        f"/api/v1/balances/group/{group_id}",
        headers=test_user_token_headers["token1"],
    )
    assert bal_resp.status_code == 200
    balances = bal_resp.json()
    assert len(balances) == 1
    assert balances[0]["user_id"] == user2_id
    assert balances[0]["owes_to_id"] == user1_id
    assert balances[0]["amount"] == 190.0


def test_monthly_summary_report_integration(client, test_user_token_headers):
    # Setup expense
    grp = client.post(
        "/api/v1/groups/",
        headers=test_user_token_headers["token1"],
        json={"name": "Reporting Group"},
    ).json()
    client.post(
        f"/api/v1/groups/{grp['id']}/members",
        headers=test_user_token_headers["token1"],
        json={"identifier": test_user_token_headers["email2"]},
    )
    client.post(
        "/api/v1/expenses/",
        headers=test_user_token_headers["token1"],
        json={
            "description": "Report Dinner",
            "amount": 100.0,
            "group_id": grp["id"],
            "split_type": "equal",
            "splits": [
                {"user_id": test_user_token_headers["user1_id"]},
                {"user_id": test_user_token_headers["user2_id"]},
            ],
        },
    )

    # Test monthly summary API against real PostgreSQL
    summary_resp = client.get(
        "/api/v1/reports/monthly-summary",
        headers=test_user_token_headers["token1"],
    )
    assert summary_resp.status_code == 200
    summaries = summary_resp.json()
    assert len(summaries) >= 1
    assert summaries[0]["total_paid"] >= 100.0
    assert "month" in summaries[0]
