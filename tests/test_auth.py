"""Tests for authentication and health endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.models.user import User


def test_health_check(client: TestClient):
    """GET /health should return 200 OK and healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "app_name" in data
    assert "timestamp" in data


def test_signup_success(client: TestClient, db_session: Session):
    """POST /signup should create a user and return 201 with public user data."""
    payload = {
        "email": "trainee@fitness.com",
        "password": "SecurePassword123!",
    }
    response = client.post("/signup", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "trainee@fitness.com"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data
    # Plaintext password and password hash must never be exposed
    assert "password" not in data
    assert "hashed_password" not in data

    # Verify directly in the database that password was hashed
    user_in_db = db_session.query(User).filter(User.email == "trainee@fitness.com").first()
    assert user_in_db is not None
    assert user_in_db.hashed_password != "SecurePassword123!"
    assert user_in_db.hashed_password.startswith("$2b$") or user_in_db.hashed_password.startswith("$2a$")


def test_signup_duplicate_email_409(client: TestClient):
    """POST /signup should return HTTP 409 Conflict if email is already registered."""
    payload = {
        "email": "duplicate@fitness.com",
        "password": "Password123!",
    }
    first_res = client.post("/signup", json=payload)
    assert first_res.status_code == 201

    # Attempt to sign up with the exact same email
    second_res = client.post("/signup", json=payload)
    assert second_res.status_code == 409
    assert "already exists" in second_res.json()["detail"].lower()


def test_signup_invalid_email_validation(client: TestClient):
    """POST /signup should reject an invalid email with HTTP 422."""
    payload = {
        "email": "not-an-email",
        "password": "ValidPassword123",
    }
    response = client.post("/signup", json=payload)
    assert response.status_code == 422


def test_signup_short_password_validation(client: TestClient):
    """POST /signup should reject passwords shorter than 6 characters with HTTP 422."""
    payload = {
        "email": "shortpass@fitness.com",
        "password": "123",
    }
    response = client.post("/signup", json=payload)
    assert response.status_code == 422


def test_login_success(client: TestClient):
    """POST /login should authenticate valid credentials and return a signed JWT token."""
    # First sign up
    client.post(
        "/signup",
        json={"email": "member@fitness.com", "password": "SecretPassword123"},
    )

    # Now log in
    response = client.post(
        "/login",
        json={"email": "member@fitness.com", "password": "SecretPassword123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # Decode and verify the JWT payload
    payload = decode_access_token(data["access_token"])
    assert payload is not None
    assert payload["sub"] == "member@fitness.com"
    assert "exp" in payload


def test_login_wrong_password_401(client: TestClient):
    """POST /login should return HTTP 401 for an incorrect password."""
    client.post(
        "/signup",
        json={"email": "athlete@fitness.com", "password": "CorrectPassword123"},
    )

    response = client.post(
        "/login",
        json={"email": "athlete@fitness.com", "password": "WrongPassword123"},
    )
    assert response.status_code == 401
    assert "invalid email or password" in response.json()["detail"].lower()


def test_login_nonexistent_email_401(client: TestClient):
    """POST /login should return HTTP 401 for an unregistered email address."""
    response = client.post(
        "/login",
        json={"email": "ghost@fitness.com", "password": "AnyPassword123"},
    )
    assert response.status_code == 401
    assert "invalid email or password" in response.json()["detail"].lower()


def test_missing_auth_token_401(client: TestClient):
    """Protected endpoints must return HTTP 401 when Authorization header is omitted."""
    response = client.get("/bookings")
    assert response.status_code == 401
    assert "missing" in response.json()["detail"].lower()


def test_invalid_auth_token_401(client: TestClient):
    """Protected endpoints must return HTTP 401 when an invalid/tampered token is provided."""
    headers = {"Authorization": "Bearer not.a.valid.jwt.token"}
    response = client.get("/bookings", headers=headers)
    assert response.status_code == 401
    assert "invalid or expired" in response.json()["detail"].lower()


def test_expired_auth_token_401(client: TestClient):
    """Protected endpoints must return HTTP 401 when an expired token is provided."""
    from datetime import timedelta
    from app.core.security import create_access_token

    # Create a user
    client.post(
        "/signup",
        json={"email": "expired_user@fitness.com", "password": "Password123!"},
    )

    # Generate a token that expired 1 hour ago
    expired_token = create_access_token(
        subject="expired_user@fitness.com",
        expires_delta=timedelta(hours=-1),
    )

    headers = {"Authorization": f"Bearer {expired_token}"}
    response = client.get("/bookings", headers=headers)
    assert response.status_code == 401
    assert "invalid or expired" in response.json()["detail"].lower()

