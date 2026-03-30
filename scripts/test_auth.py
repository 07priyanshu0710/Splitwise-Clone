
import requests
import sys
import uuid

BASE_URL = "http://localhost:8000/api/v1"

def test_auth():
    # Generate random email to avoid collision and ensure fresh hash
    random_str = str(uuid.uuid4())[:8]
    email = f"test_{random_str}@example.com"
    password = "password123"
    full_name = "Test User"
    
    print(f"1. Registering user {email}...")
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json={
            "email": email,
            "password": password,
            "full_name": full_name
        })
        if response.status_code == 200:
            print("   Registration Successful:", response.json())
        else:
            print("   Registration Failed:", response.text)
            return
    except Exception as e:
        print(f"   Connection failed: {e}")
        return

    # 2. Login
    print("\n2. Logging in...")
    response = requests.post(f"{BASE_URL}/auth/login", data={
        "username": email,
        "password": password
    })
    
    if response.status_code != 200:
        print("   Login Failed:", response.text)
        return

    token_data = response.json()
    access_token = token_data["access_token"]
    print("   Login Successful. Token obtained.")

    headers = {"Authorization": f"Bearer {access_token}"}

    # 3. Get Profile
    print("\n3. Fetching Profile...")
    response = requests.get(f"{BASE_URL}/users/me", headers=headers)
    
    if response.status_code == 200:
        print("   Profile Fetched Successfully:", response.json())
        user_id = response.json().get("id")
    else:
        print("   Profile Fetch Failed:", response.text)
        return

    # 4. Update Profile
    print("\n4. Updating Profile...")
    new_name = f"Updated Name {random_str}"
    response = requests.put(f"{BASE_URL}/users/me", headers=headers, json={
        "full_name": new_name
    })

    if response.status_code == 200:
        print("   Update Successful:", response.json())
        if response.json().get("full_name") == new_name:
            print("   Verification: Name is updated correctly.")
        else:
            print("   Verification Failed: Name mismatch.")
    else:
        print("   Update Failed:", response.text)

if __name__ == "__main__":
    test_auth()
