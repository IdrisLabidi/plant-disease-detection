import logging
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..db import get_db
from ..deps import current_user
from ..models import OAuthIdentity, RefreshToken, User
from ..oauth.base import OAuthProvider, ProviderIdentity
from ..oauth.facebook import FacebookOAuthProvider
from ..oauth.google import GoogleOAuthProvider
from ..schemas import FacebookLoginRequest, GoogleLoginRequest, TokenResponse, UserResponse
from ..security import issue_access_token, new_refresh_token

router = APIRouter(prefix="/auth", tags=["oauth"])
logger = logging.getLogger("auth.events")


def provider_registry() -> dict[str, OAuthProvider]:
    return {"google": GoogleOAuthProvider(), "facebook": FacebookOAuthProvider()}


def _identity(
    provider_name: str,
    identity: ProviderIdentity,
    db: Session,
) -> tuple[User, bool]:
    existing = db.scalar(
        select(OAuthIdentity).where(
            OAuthIdentity.provider == provider_name,
            OAuthIdentity.provider_user_id == identity.subject,
        )
    )
    if existing:
        user = db.get(User, existing.user_id)
        if not user or user.deleted_at:
            raise HTTPException(status_code=401, detail="Identity is unavailable")
        logger.info(
            "auth_event",
            extra={"event": "oauth_login", "provider": provider_name, "outcome": "existing_identity"},
        )
        return user, False

    email = identity.email.strip().lower() if identity.email else None

    if identity.email_verified and email:
        verified_match = db.scalar(
            select(User).where(
                User.email == email,
                User.deleted_at.is_(None),
                User.email_verified.is_(True),
            )
        )
        if verified_match:
            user = verified_match
            is_new = False
        else:
            unverified_match = db.scalar(
                select(User).where(
                    User.email == email,
                    User.deleted_at.is_(None),
                    User.email_verified.is_(False),
                )
            )
            if unverified_match:
                unverified_match.email_verified = True
                unverified_match.password_hash = None
                db.query(RefreshToken).filter(RefreshToken.user_id == unverified_match.id).update(
                    {RefreshToken.revoked_at: datetime.now(UTC)},
                    synchronize_session=False,
                )
                logger.warning(
                    "auth_event",
                    extra={
                        "event": "account_takeover_protection",
                        "provider": provider_name,
                        "outcome": "verified_provider_claim",
                    },
                )
                user = unverified_match
                is_new = False
            else:
                user = User(
                    email=email,
                    email_verified=True,
                    display_name=identity.name,
                    password_hash=None,
                )
                is_new = True
    else:
        user = User(
            email=None,
            email_verified=False,
            display_name=identity.name,
            password_hash=None,
        )
        is_new = True

    db.add(user)
    db.flush()
    db.add(
        OAuthIdentity(
            user_id=user.id,
            provider=provider_name,
            provider_user_id=identity.subject,
            email_at_link=email,
        )
    )
    db.commit()
    db.refresh(user)
    logger.info(
        "auth_event",
        extra={"event": "oauth_login", "provider": provider_name, "outcome": "created" if is_new else "linked"},
    )
    return user, is_new


def _tokens(user: User, db: Session, request: Request) -> TokenResponse:
    settings = get_settings()
    access, expires_in = issue_access_token(user.id)
    raw, token_hash = new_refresh_token()
    db.add(
        RefreshToken(
            user_id=user.id,
            family_id=uuid.uuid4(),
            token_hash=token_hash,
            expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_days),
            user_agent=request.headers.get("user-agent"),
        )
    )
    db.commit()
    return TokenResponse(
        access_token=access,
        refresh_token=raw,
        expires_in=expires_in,
        user=UserResponse.model_validate(user),
    )


def _verify(provider_name: str, credentials: str, nonce: str | None = None) -> ProviderIdentity:
    provider = provider_registry().get(provider_name)
    if not provider:
        raise HTTPException(status_code=404, detail="Unknown provider")
    try:
        return provider.verify(credentials, nonce)
    except (ValueError, HTTPException) as exc:
        raise HTTPException(status_code=401, detail="Invalid OAuth credentials") from exc


@router.post("/oauth/google", response_model=TokenResponse)
def google_login(payload: GoogleLoginRequest, request: Request, db: Session = Depends(get_db)):
    identity = _verify("google", payload.id_token, payload.nonce)
    user, is_new = _identity("google", identity, db)
    response = _tokens(user, db, request)
    return response.model_copy(update={"is_new_user": is_new})


@router.post("/oauth/facebook", response_model=TokenResponse)
def facebook_login(payload: FacebookLoginRequest, request: Request, db: Session = Depends(get_db)):
    identity = _verify("facebook", payload.access_token)
    user, is_new = _identity("facebook", identity, db)
    response = _tokens(user, db, request)
    return response.model_copy(update={"is_new_user": is_new})


@router.post("/link/{provider_name}")
def link_identity(
    provider_name: str,
    credentials: dict,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    if provider_name not in {"google", "facebook"}:
        raise HTTPException(status_code=404, detail="Unknown provider")
    credential = credentials.get("id_token") if provider_name == "google" else credentials.get("access_token")
    nonce = credentials.get("nonce") if provider_name == "google" else None
    if not isinstance(credential, str):
        raise HTTPException(status_code=422, detail="Invalid OAuth credentials")

    identity = _verify(provider_name, credential, nonce)
    existing = db.scalar(
        select(OAuthIdentity).where(
            OAuthIdentity.provider == provider_name,
            OAuthIdentity.provider_user_id == identity.subject,
        )
    )
    if existing:
        if existing.user_id != user.id:
            raise HTTPException(status_code=409, detail="Identity is linked to another account")
        return {"message": "Identity already linked"}

    db.add(
        OAuthIdentity(
            user_id=user.id,
            provider=provider_name,
            provider_user_id=identity.subject,
            email_at_link=identity.email.lower() if identity.email else None,
        )
    )
    db.commit()
    logger.info(
        "auth_event",
        extra={"event": "link", "provider": provider_name, "outcome": "linked"},
    )
    return {"message": "Identity linked"}


@router.delete("/link/{provider_name}")
def unlink_identity(
    provider_name: str,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    identity = db.scalar(
        select(OAuthIdentity).where(
            OAuthIdentity.user_id == user.id,
            OAuthIdentity.provider == provider_name,
        )
    )
    if not identity:
        raise HTTPException(status_code=404, detail="Identity is not linked")

    identity_count = len(user.oauth_identities)
    if user.password_hash is None and identity_count <= 1:
        raise HTTPException(status_code=409, detail="Cannot remove the last login method")

    db.delete(identity)
    db.commit()
    logger.info(
        "auth_event",
        extra={"event": "unlink", "provider": provider_name, "outcome": "unlinked"},
    )
    return {"message": "Identity unlinked"}
