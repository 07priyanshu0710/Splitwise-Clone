import requests
import sys
import uuid

BASE_URL = "http://localhost:8000/api/v1"

def create_user_and_login(prefix="user"):
    random_str = str(uuid.uuid4())[:8]
    email = f"{prefix}_{random_str}@example.com"
    password = "password123"
    
    # Register
    res = requests.post(f"{BASE_URL}/auth/register", json={
        "email": email, "password": password, "full_name": f"{prefix} {random_str}"
    })
    res.raise_for_status()
    
    # Login
    res = requests.post(f"{BASE_URL}/auth/login", data={
        "username": email, "password": password
    })
    res.raise_for_status()
    
    token = res.json()["access_token"]
    
    # Get Profile to get user_id
    res = requests.get(f"{BASE_URL}/users/me", headers={"Authorization": f"Bearer {token}"})
    user_id = res.json()["id"]
    
    return token, user_id, email

def run_test():
    try:
        print("1. Setting up two users...")
        token1, user1_id, email1 = create_user_and_login("alice")
        token2, user2_id, email2 = create_user_and_login("bob")
        
        headers1 = {"Authorization": f"Bearer {token1}"}
        headers2 = {"Authorization": f"Bearer {token2}"}

        print("\n2. User 1 creates a group...")
        res = requests.post(f"{BASE_URL}/groups/", headers=headers1, json={
            "name": "Weekend Trip",
            "description": "Expenses for the weekend trip"
        })
        res.raise_for_status()
        group_id = res.json()["id"]
        print(f"   Group created with ID {group_id}")

        print(f"\n3. User 1 adds User 2 ({email2}) to the group...")
        res = requests.post(f"{BASE_URL}/groups/{group_id}/members", headers=headers1, json={
            "email": email2
        })
        res.raise_for_status()
        print("   User 2 added to group.")

        print("\n4. User 1 adds an EQUAL expense of $100...")
        expense_data = {
            "description": "Dinner",
            "amount": 100.0,
            "group_id": group_id,
            "split_type": "equal",
            "splits": [
                {"user_id": user1_id},
                {"user_id": user2_id}
            ]
        }
        res = requests.post(f"{BASE_URL}/expenses/", headers=headers1, json=expense_data)
        if res.status_code != 200:
            print("   Failed to add expense:", res.text)
            return
            
        expense = res.json()
        print(f"   Expense created with ID {expense['id']}")
        
        # Verify Equal Split Amounts
        splits = expense["splits"]
        amounts = [s["amount"] for s in splits]
        print(f"   Verified equal split amounts: {amounts}")

        print("\n5. User 1 adds a PERCENTAGE expense of $200 (60% User 1, 40% User 2)...")
        expense_data_perc = {
            "description": "Hotel",
            "amount": 200.0,
            "group_id": group_id,
            "split_type": "percentage",
            "splits": [
                {"user_id": user1_id, "percentage": 60.0},
                {"user_id": user2_id, "percentage": 40.0}
            ]
        }
        res = requests.post(f"{BASE_URL}/expenses/", headers=headers1, json=expense_data_perc)
        if res.status_code != 200:
            print("   Failed to add expense:", res.text)
            return
        
        expense_perc = res.json()
        print(f"   Percentage Expense created with ID {expense_perc['id']}")
        
        print("\n6. Fetching group expenses for User 2...")
        res = requests.get(f"{BASE_URL}/expenses/group/{group_id}", headers=headers2)
        res.raise_for_status()
        group_expenses = res.json()
        print(f"   User 2 fetched {len(group_expenses)} expenses for the group.")

        print("\n✅ All tests passed!")
        
    except requests.exceptions.HTTPError as e:
        print(f"\n❌ Error during HTTP request: {e.response.status_code} - {e.response.text}")

if __name__ == "__main__":
    run_test()
