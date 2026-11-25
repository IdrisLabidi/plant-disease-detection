from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import current_user
from ..models import EmailToken, OAuthIdentity, RefreshToken, Scan, User
from ..schemas import DeleteAccountRequest, MeUpdateRequest, UserResponse
from ..security import verify_password

router = APIRouter(prefix="/me", tags=["me"])


@router.get("", response_model=UserResponse)
def get_me(user: User = Depends(current_user)) -> User:
    return user


@router.patch("", response_model=UserResponse)
def update_me(
    payload: MeUpdateRequest,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> User:
    user.display_name = payload.display_name
    db.commit()
    db.refresh(user)
    return user


@router.get("/identities")
def get_identities(
    user: User = Depends(current_user),
) -> list[dict[str, str]]:
    return [
        {"provider": identity.provider, "email_at_link": identity.email_at_link or ""}
        for identity in user.oauth_identities
    ]


@router.delete("", status_code=204)
def delete_me(
    request: Request,
    payload: DeleteAccountRequest | None = None,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> None:
    payload = payload or DeleteAccountRequest()
    if user.password_hash:
        if not verify_password(payload.current_password or "", user.password_hash):
            raise HTTPException(status_code=401, detail="Re-authentication required")
    else:
        if not payload.provider or not payload.provider_token:
            raise HTTPException(status_code=401, detail="Re-authentication required")
        from ..oauth.base import OAuthProvider
        from ..oauth.facebook import FacebookOAuthProvider
        from ..oauth.google import GoogleOAuthProvider

        providers: dict[str, OAuthProvider] = {
            "google": GoogleOAuthProvider(),
            "facebook": FacebookOAuthProvider(),
        }
        provider = providers.get(payload.provider)
        if not provider:
            raise HTTPException(status_code=401, detail="Re-authentication required")
        try:
            identity = provider.verify(payload.provider_token)
        except ValueError:
            raise HTTPException(status_code=401, detail="Re-authentication required") from None
        linked = db.scalar(
            select(OAuthIdentity).where(
                OAuthIdentity.user_id == user.id,
                OAuthIdentity.provider == payload.provider,
                OAuthIdentity.provider_user_id == identity.subject,
            )
        )
        if not linked:
            raise HTTPException(status_code=401, detail="Re-authentication required")
    user.deleted_at = datetime.now(UTC)
    user.email = None
    user.password_hash = None
    db.query(OAuthIdentity).filter(OAuthIdentity.user_id == user.id).delete()
    db.query(EmailToken).filter(EmailToken.user_id == user.id).delete()
    db.query(RefreshToken).filter(RefreshToken.user_id == user.id).delete()
    scans = db.scalars(select(Scan).where(Scan.user_id == user.id)).all()
    storage = getattr(request.app.state, "storage", None)
    if storage:
        for scan in scans:
            storage.delete(scan.image_path)
            storage.delete(scan.mask_path)
    db.query(Scan).filter(Scan.user_id == user.id).delete()
    db.commit()
