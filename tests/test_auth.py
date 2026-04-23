"""Tests for authentication endpoints: register, login, and /auth/me."""
import json

import pytest


# ---------------------------------------------------------------------------
# POST /api/auth/register
# ---------------------------------------------------------------------------


class TestRegister:
    def test_register_returns_201_and_token(self, client):
        res = client.post(
            "/api/auth/register",
            data=json.dumps(
                {
                    "email": "new@example.com",
                    "password": "password123",
                    "full_name": "New User",
                }
            ),
            content_type="application/json",
        )
        assert res.status_code == 201
        data = res.get_json()
        assert "access_token" in data
        assert data["user"]["email"] == "new@example.com"
        assert "password" not in data["user"]

    def test_register_duplicate_email_returns_409(self, client):
        payload = json.dumps(
            {"email": "dup@example.com", "password": "password123"}
        )
        client.post("/api/auth/register", data=payload, content_type="application/json")
        res = client.post(
            "/api/auth/register", data=payload, content_type="application/json"
        )
        assert res.status_code == 409

    def test_register_missing_email_returns_422(self, client):
        res = client.post(
            "/api/auth/register",
            data=json.dumps({"password": "password123"}),
            content_type="application/json",
        )
        assert res.status_code == 422

    def test_register_short_password_returns_422(self, client):
        res = client.post(
            "/api/auth/register",
            data=json.dumps({"email": "short@test.com", "password": "abc"}),
            content_type="application/json",
        )
        assert res.status_code == 422

    def test_register_invalid_email_returns_422(self, client):
        res = client.post(
            "/api/auth/register",
            data=json.dumps({"email": "not-an-email", "password": "password123"}),
            content_type="application/json",
        )
        assert res.status_code == 422


# ---------------------------------------------------------------------------
# POST /api/auth/login
# ---------------------------------------------------------------------------


class TestLogin:
    def _register(self, client, email="login@test.com", password="password123"):
        client.post(
            "/api/auth/register",
            data=json.dumps({"email": email, "password": password}),
            content_type="application/json",
        )

    def test_login_success(self, client):
        self._register(client)
        res = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "login@test.com", "password": "password123"}),
            content_type="application/json",
        )
        assert res.status_code == 200
        data = res.get_json()
        assert "access_token" in data
        assert data["user"]["email"] == "login@test.com"

    def test_login_wrong_password_returns_401(self, client):
        self._register(client)
        res = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "login@test.com", "password": "wrongpass"}),
            content_type="application/json",
        )
        assert res.status_code == 401

    def test_login_nonexistent_user_returns_401(self, client):
        res = client.post(
            "/api/auth/login",
            data=json.dumps({"email": "ghost@test.com", "password": "password123"}),
            content_type="application/json",
        )
        assert res.status_code == 401


# ---------------------------------------------------------------------------
# GET /api/auth/me  (protected)
# ---------------------------------------------------------------------------


class TestMe:
    def test_me_returns_current_user(self, client, auth_headers, test_user):
        res = client.get("/api/auth/me", headers=auth_headers)
        assert res.status_code == 200
        data = res.get_json()
        assert data["user"]["email"] == test_user.email

    def test_me_without_token_returns_401(self, client):
        res = client.get("/api/auth/me")
        assert res.status_code == 401

    def test_me_with_invalid_token_returns_401(self, client):
        res = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert res.status_code == 401


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


class TestHealth:
    def test_health_endpoint(self, client):
        res = client.get("/health")
        assert res.status_code == 200
        assert res.get_json()["status"] == "healthy"
