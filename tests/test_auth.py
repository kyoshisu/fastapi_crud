from fastapi.testclient import TestClient
import pytest

@pytest.fixture
def unauth_client(client):
    client.cookies.clear()
    return client

def test_register_success(client):
    response = client.post("/auth/register", json={
        "username": "newuser",
        "email": "new@example.com",
        "password": "SecurePass123"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "new@example.com"
    assert "id" in data

def test_register_duplicate_username(client, registered_user):
    response = client.post("/auth/register", json={
        "username": "testuser",
        "email": "another@example.com",
        "password": "SecurePass123"
    })
    assert response.status_code == 400

def test_login_success(client, registered_user):
    response = client.post("/auth/login", json={
        "username": registered_user["username"],
        "password": registered_user["password"]
    })
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert data["user_id"] is not None

def test_login_wrong_password(client, registered_user):
    response = client.post("/auth/login", json={
        "username": registered_user["username"],
        "password": "WrongPassword123"
    })
    assert response.status_code == 401

def test_logout_success(client, registered_user):
    login_response = client.post("/auth/login", json={
        "username": registered_user["username"],
        "password": registered_user["password"]
    })
    cookies = login_response.cookies
    response = client.post("/auth/logout", cookies=cookies)
    assert response.status_code == 200

def test_logout_without_token(unauth_client):
    response = unauth_client.post("/auth/logout")
    assert response.status_code == 200

def test_get_students_unauthorized(unauth_client):
    response = unauth_client.get("/students")
    assert response.status_code == 401

def test_get_students_authorized(client, registered_user):
    login_response = client.post("/auth/login", json={
        "username": registered_user["username"],
        "password": registered_user["password"]
    })
    cookies = login_response.cookies
    response = client.get("/students", cookies=cookies)
    assert response.status_code in [200, 404]

def test_get_student_by_id_unauthorized(unauth_client):
    response = unauth_client.get("/students/1")
    assert response.status_code == 401

def test_get_nonexistent_student(client, registered_user):
    login_response = client.post("/auth/login", json={
        "username": registered_user["username"],
        "password": registered_user["password"]
    })
    cookies = login_response.cookies
    response = client.get("/students/99999", cookies=cookies)
    assert response.status_code == 404

def test_create_student_unauthorized(unauth_client):
    response = unauth_client.post("/students", params={
        "last_name": "Иванов",
        "first_name": "Иван",
        "faculty": "АВТФ"
    })
    assert response.status_code == 401

def test_create_student_success(client, registered_user):
    login_response = client.post("/auth/login", json={
        "username": registered_user["username"],
        "password": registered_user["password"]
    })
    cookies = login_response.cookies
    response = client.post("/students", cookies=cookies, params={
        "last_name": "Петров",
        "first_name": "Петр",
        "faculty": "ФПМИ"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["last_name"] == "Петров"
    assert data["first_name"] == "Петр"
    assert data["faculty"] == "ФПМИ"