from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import current_user
from ..models import RefreshToken, User
from ..schemas import MeUpdateRequest, UserResponse

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
def delete_me(user: User = Depends(current_user), db: Session = Depends(get_db)) -> None:
    user.deleted_at = datetime.now(UTC)
    user.email = None
    user.password_hash = None
    db.query(RefreshToken).filter(RefreshToken.user_id == user.id).delete()
    db.commit()
