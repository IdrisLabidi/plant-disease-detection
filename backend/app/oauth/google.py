from google.auth.transport import requests
from google.oauth2 import id_token

from ..config import get_settings
from .base import ProviderIdentity


class GoogleOAuthProvider:
    provider = "google"

    def verify(self, credentials: str, nonce: str | None = None) -> ProviderIdentity:
        settings = get_settings()
        if not settings.google_client_ids:
            raise ValueError("Google OAuth is not configured")

        claims = None
        for audience in settings.google_client_ids:
            try:
                claims = id_token.verify_oauth2_token(credentials, requests.Request(), audience)
                break
            except ValueError:
                continue
        if claims is None:
            raise ValueError("Invalid Google ID token")

        issuer = claims.get("iss")
        if issuer not in {"accounts.google.com", "https://accounts.google.com"}:
            raise ValueError("Invalid Google issuer")
        if nonce is not None and claims.get("nonce") != nonce:
            raise ValueError("Invalid Google nonce")

        email = claims.get("email")
        return ProviderIdentity(
            provider="google",
            subject=str(claims["sub"]),
            email=email.lower() if isinstance(email, str) else None,
            email_verified=claims.get("email_verified") is True,
            name=claims.get("name"),
        )
