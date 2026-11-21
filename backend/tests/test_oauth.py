import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.db import SessionLocal
from app.main import app
from app.models import RefreshToken, User
from app.oauth.base import ProviderIdentity
from app.security import hash_password


class FakeGoogle:
    def __init__(self, result: ProviderIdentity):
        self.result = result

    def verify(self, credentials: str, nonce: str | None = None) -> ProviderIdentity:
        if credentials.startswith("wrong"):
            raise ValueError("bad credentials")
        return self.result


class FakeFacebook:
    def __init__(self, result: ProviderIdentity):
        self.result = result

    def verify(self, credentials: str, nonce: str | None = None) -> ProviderIdentity:
        if credentials.startswith("wrong"):
            raise ValueError("bad credentials")
        return self.result


def set_providers(monkeypatch, google=None, facebook=None):
    from app.routers import oauth

    registry = {}
    if google:
        registry["google"] = google
    if facebook:
        registry["facebook"] = facebook
    monkeypatch.setattr(oauth, "provider_registry", lambda: registry)


def test_oauth_existing_identity_logs_in(monkeypatch):
    set_providers(
        monkeypatch,
        google=FakeGoogle(ProviderIdentity("google", "subject-1", "person@example.com", True, "Person")),
    )
    with TestClient(app) as client:
        first = client.post("/auth/oauth/google", json={"id_token": "valid-token-1234567890"})
        assert first.status_code == 200
        assert first.json()["is_new_user"] is True
        second = client.post("/auth/oauth/google", json={"id_token": "valid-token-1234567890"})
        assert second.status_code == 200
        assert second.json()["is_new_user"] is False


def test_verified_email_links_existing_user(monkeypatch):
    set_providers(
        monkeypatch,
        google=FakeGoogle(ProviderIdentity("google", "subject-link", "linked@example.com", True, "Linked")),
    )
    with SessionLocal() as db:
        db.add(
            User(
                email="linked@example.com",
                email_verified=True,
                display_name="Existing",
                password_hash=hash_password("StrongPassword!42"),
            )
        )
        db.commit()
    with TestClient(app) as client:
        response = client.post("/auth/oauth/google", json={"id_token": "valid-token-1234567890"})
        assert response.status_code == 200
        assert response.json()["is_new_user"] is False


def test_unverified_email_takeover_is_safe(monkeypatch):
    set_providers(
        monkeypatch,
        google=FakeGoogle(ProviderIdentity("google", "subject-takeover", "takeover@example.com", True, "Verified")),
    )
    with SessionLocal() as db:
        victim = User(
            email="takeover@example.com",
            email_verified=False,
            password_hash=hash_password("OldPassword!42"),
        )
        db.add(victim)
        db.flush()
        refresh = RefreshToken(
            user_id=victim.id,
            family_id=uuid.uuid4(),
            token_hash="a" * 64,
            expires_at=datetime.now(UTC),
        )
        db.add(refresh)
        db.commit()
        victim_id = victim.id
        refresh_id = refresh.id

    with TestClient(app) as client:
        response = client.post("/auth/oauth/google", json={"id_token": "valid-token-1234567890"})
        assert response.status_code == 200
    with SessionLocal() as db:
        victim = db.get(User, victim_id)
        refresh = db.get(RefreshToken, refresh_id)
        assert victim.email_verified is True
        assert victim.password_hash is None
        assert refresh.revoked_at is not None


def test_facebook_missing_email_creates_distinct_user(monkeypatch):
    set_providers(
        monkeypatch,
        facebook=FakeFacebook(ProviderIdentity("facebook", "facebook-no-email", None, False, "Facebook User")),
    )
    with TestClient(app) as client:
        response = client.post("/auth/oauth/facebook", json={"access_token": "valid-token-1234567890"})
        assert response.status_code == 200
        assert response.json()["user"]["email"] is None


def test_invalid_provider_credentials_are_rejected(monkeypatch):
    set_providers(
        monkeypatch,
        google=FakeGoogle(ProviderIdentity("google", "unused", None, False, None)),
    )
    with TestClient(app) as client:
        response = client.post("/auth/oauth/google", json={"id_token": "wrong-token-1234567890"})
        assert response.status_code == 401


def test_unlink_refuses_last_login_method(monkeypatch):
    set_providers(
        monkeypatch,
        google=FakeGoogle(ProviderIdentity("google", "subject-unlink", "unlink@example.com", True, "Unlink")),
    )
    with TestClient(app) as client:
        login = client.post("/auth/oauth/google", json={"id_token": "valid-token-1234567890"})
        access = login.json()["access_token"]
        response = client.delete(
            "/auth/link/google",
            headers={"Authorization": f"Bearer {access}"},
        )
        assert response.status_code == 409


def test_google_wrong_audience_expired_and_unverified_claims(monkeypatch):
    from app.oauth import google

    monkeypatch.setattr(
        google,
        "get_settings",
        lambda: SimpleNamespace(google_client_ids=["expected-client"]),
    )

    def reject_all(*args, **kwargs):
        raise ValueError("invalid token")

    monkeypatch.setattr(google.id_token, "verify_oauth2_token", reject_all)
    provider = google.GoogleOAuthProvider()
    with pytest.raises(ValueError):
        provider.verify("audience-or-expired-token")

    def unverified_claims(*args, **kwargs):
        return {
            "iss": "accounts.google.com",
            "sub": "google-subject",
            "email": "UNVERIFIED@EXAMPLE.COM",
            "email_verified": False,
            "name": "Unverified",
        }

    monkeypatch.setattr(google.id_token, "verify_oauth2_token", unverified_claims)
    identity = provider.verify("valid-token-1234567890")
    assert identity.email == "unverified@example.com"
    assert identity.email_verified is False
