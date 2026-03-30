import pytest

def test_register_user(client):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "newuser@example.com", "password": "securepassword", "full_name": "New User"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["full_name"] == "New User"
    assert "id" in data

def test_register_duplicate_user(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "dup@example.com", "password": "securepassword", "full_name": "Dup User"}
    )
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "dup@example.com", "password": "securepassword", "full_name": "Dup User"}
    )
    assert response.status_code == 400

def test_login(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "login@example.com", "password": "securepassword", "full_name": "Login User"}
    )
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "login@example.com", "password": "securepassword"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    
def test_login_invalid(client):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "nobody@example.com", "password": "securepassword"}
    )
    assert response.status_code == 401
