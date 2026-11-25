import re

from fastapi.testclient import TestClient

from app.main import app


def test_register_login_and_generic_login_error():
    with TestClient(app) as client:
        registered = client.post(
            "/auth/register",
            json={"email": "auth@example.com", "password": "StrongPassword!42"},
        )
        assert registered.status_code == 201
        token = registered.json()["access_token"]
        assert client.get("/me", headers={"Authorization": f"Bearer {token}"}).status_code == 200

        wrong_password = client.post(
            "/auth/login",
            json={"email": "auth@example.com", "password": "wrong-password"},
        )
        unknown_email = client.post(
            "/auth/login",
            json={"email": "unknown@example.com", "password": "wrong-password"},
        )
        assert wrong_password.status_code == unknown_email.status_code == 401
        assert wrong_password.json() == unknown_email.json()


def test_refresh_rotation_and_reuse_revokes_family():
    with TestClient(app) as client:
        response = client.post(
            "/auth/register",
            json={"email": "rotation@example.com", "password": "StrongPassword!42"},
        )
        original = response.json()["refresh_token"]
        rotated = client.post("/auth/refresh", json={"refresh_token": original})
        assert rotated.status_code == 200
        replacement = rotated.json()["refresh_token"]

        reused = client.post("/auth/refresh", json={"refresh_token": original})
        assert reused.status_code == 401
        assert client.post("/auth/refresh", json={"refresh_token": replacement}).status_code == 401


def test_email_verification_token_is_single_use(capsys):
    with TestClient(app) as client:
        response = client.post(
            "/auth/register",
            json={"email": "verify@example.com", "password": "StrongPassword!42"},
        )
        assert response.status_code == 201
        token = re.search(r"Use this token: ([A-Za-z0-9_-]+)", capsys.readouterr().out).group(1)
        assert client.post("/auth/email/verify", json={"token": token}).status_code == 200
        assert client.post("/auth/email/verify", json={"token": token}).status_code == 400
