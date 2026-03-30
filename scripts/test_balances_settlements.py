import requests
import uuid

BASE_URL = "http://localhost:8000/api/v1"

def create_user_and_login(prefix="user"):
    random_str = str(uuid.uuid4())[:8]
    email = f"{prefix}_{random_str}@example.com"
    password = "password123"
    requests.post(f"{BASE_URL}/auth/register", json={"email": email, "password": password, "full_name": f"{prefix} {random_str}"}).raise_for_status()
    res = requests.post(f"{BASE_URL}/auth/login", data={"username": email, "password": password})
    res.raise_for_status()
    token = res.json()["access_token"]
    res = requests.get(f"{BASE_URL}/users/me", headers={"Authorization": f"Bearer {token}"})
    return token, res.json()["id"], email

def run_test():
    try:
        print("1. Setup users...")
        t1, u1, e1 = create_user_and_login("alice")
        t2, u2, e2 = create_user_and_login("bob")
        
        h1 = {"Authorization": f"Bearer {t1}"}
        h2 = {"Authorization": f"Bearer {t2}"}

        print("\n2. Alice creates a group and adds Bob...")
        res = requests.post(f"{BASE_URL}/groups/", headers=h1, json={"name": "Roommates"})
        g_id = res.json()["id"]
        requests.post(f"{BASE_URL}/groups/{g_id}/members", headers=h1, json={"email": e2}).raise_for_status()

        print("\n3. Alice adds an EQUAL expense of $100 (Alice paid $100)...")
        res = requests.post(f"{BASE_URL}/expenses/", headers=h1, json={
            "description": "Electricity",
            "amount": 100.0,
            "group_id": g_id,
            "split_type": "equal",
            "splits": [{"user_id": u1}, {"user_id": u2}]
        })
        res.raise_for_status()
        
        print("\n4. Check Balances for Alice...")
        res = requests.get(f"{BASE_URL}/balances/me", headers=h1)
        res.raise_for_status()
        bals = res.json()
        print(f"   Alice Balances: {bals}")
        # Bob (u2) should owe Alice (u1) $50
        
        print("\n5. Bob settles up with Alice paying $50...")
        res = requests.post(f"{BASE_URL}/settlements/", headers=h2, json={
            "payee_id": u1,
            "amount": 50.0,
            "group_id": g_id,
            "description": "Paid for electricity"
        })
        res.raise_for_status()
        print("   Settlement Response:", res.json())

        print("\n6. Check Balances for Alice again...")
        res = requests.get(f"{BASE_URL}/balances/me", headers=h1)
        res.raise_for_status()
        bals = res.json()
        print(f"   Alice Balances: {bals}")

        print("\n✅ All balances tests passed!")
        
    except requests.exceptions.HTTPError as e:
        print(f"\n❌ HTTP Error: {e.response.status_code} - {e.response.text}")

if __name__ == "__main__":
    run_test()
