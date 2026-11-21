import httpx

from ..config import get_settings
from .base import ProviderIdentity


class FacebookOAuthProvider:
    provider = "facebook"

    def verify(self, credentials: str, nonce: str | None = None) -> ProviderIdentity:
        settings = get_settings()
        if not settings.facebook_app_id or not settings.facebook_app_secret:
            raise ValueError("Facebook OAuth is not configured")

        base = f"https://graph.facebook.com/{settings.facebook_graph_version}"
        app_token = f"{settings.facebook_app_id}|{settings.facebook_app_secret.get_secret_value()}"
        try:
            with httpx.Client(timeout=5.0) as client:
                debug = client.get(
                    f"{base}/debug_token",
                    params={"input_token": credentials, "access_token": app_token},
                )
                debug.raise_for_status()
                data = debug.json().get("data", {})
                if not data.get("is_valid") or str(data.get("app_id")) != settings.facebook_app_id:
                    raise ValueError("Invalid Facebook access token")
                subject = data.get("user_id")
                if not subject:
                    raise ValueError("Invalid Facebook access token")

                profile = client.get(
                    f"{base}/me",
                    params={"fields": "id,name,email", "access_token": credentials},
                )
                profile.raise_for_status()
                body = profile.json()
                if str(body.get("id")) != str(subject):
                    raise ValueError("Invalid Facebook profile")
        except (httpx.HTTPError, ValueError) as exc:
            raise ValueError("Invalid Facebook access token") from exc

        email = body.get("email")
        return ProviderIdentity(
            provider="facebook",
            subject=str(body["id"]),
            email=email.lower() if isinstance(email, str) else None,
            email_verified=False,
            name=body.get("name"),
        )
