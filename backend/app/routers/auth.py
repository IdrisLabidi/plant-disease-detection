import secrets
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..db import get_db
from ..deps import current_user
from ..email import get_email_sender
from ..models import EmailToken, RefreshToken, User
from ..schemas import (
    EmailRequest,
    LoginRequest,
    PasswordChangeRequest,
    PasswordResetRequest,
    RefreshRequest,
    RegisterRequest,
    TokenRequest,
    TokenResponse,
    UserResponse,
)
from ..security import (
    hash_password,
    hash_token,
    issue_access_token,
    new_refresh_token,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _email(value: str) -> str:
    return value.strip().lower()


def _expired(value: datetime) -> bool:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value <= datetime.now(UTC)


def _tokens(user: User, db: Session, request: Request, family_id: uuid.UUID | None = None) -> TokenResponse:
    settings = get_settings()
    access, expires_in = issue_access_token(user.id)
    raw, token_hash = new_refresh_token()
    db.add(
        RefreshToken(
            user_id=user.id,
            family_id=family_id or uuid.uuid4(),
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


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(payload: RegisterRequest, request: Request, db: Session = Depends(get_db)) -> TokenResponse:
    email = _email(str(payload.email))
    if db.scalar(select(User).where(User.email == email, User.deleted_at.is_(None))):
        raise HTTPException(status_code=409, detail="An account already exists")
    user = User(email=email, display_name=payload.display_name, password_hash=hash_password(payload.password))
    db.add(user)
    db.flush()
    token = secrets.token_urlsafe(32)
    db.add(
        EmailToken(
            user_id=user.id,
            purpose="verify",
            token_hash=hash_token(token),
            expires_at=datetime.now(UTC) + timedelta(hours=24),
        )
    )
    db.commit()
    get_email_sender(get_settings()).send(email, "Verify your email", f"Use this token: {token}")
    return _tokens(user, db, request)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == _email(str(payload.email)), User.deleted_at.is_(None)))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return _tokens(user, db, request)


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, request: Request, db: Session = Depends(get_db)) -> TokenResponse:
    now = datetime.now(UTC)
    stored = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_token(payload.refresh_token)))
    if not stored or _expired(stored.expires_at):
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    if stored.revoked_at:
        db.query(RefreshToken).filter(RefreshToken.family_id == stored.family_id).update(
            {RefreshToken.revoked_at: now}, synchronize_session=False
        )
        db.commit()
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    stored.revoked_at = now
    user = db.get(User, stored.user_id)
    if not user or user.deleted_at:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    response = _tokens(user, db, request, stored.family_id)
    replacement = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_token(response.refresh_token)))
    if replacement:
        stored.replaced_by = replacement.id
    db.commit()
    return response


@router.post("/logout", status_code=204)
def logout(payload: RefreshRequest, db: Session = Depends(get_db)) -> None:
    token = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_token(payload.refresh_token)))
    if token:
        db.query(RefreshToken).filter(RefreshToken.family_id == token.family_id).update(
            {RefreshToken.revoked_at: datetime.now(UTC)}, synchronize_session=False
        )
        db.commit()


@router.post("/logout-all", status_code=204)
def logout_all(user: User = Depends(current_user), db: Session = Depends(get_db)) -> None:
    db.query(RefreshToken).filter(RefreshToken.user_id == user.id).update(
        {RefreshToken.revoked_at: datetime.now(UTC)}, synchronize_session=False
    )
    db.commit()


@router.post("/email/verify")
def verify_email(payload: TokenRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    record = db.scalar(select(EmailToken).where(EmailToken.token_hash == hash_token(payload.token)))
    if not record or record.purpose != "verify" or record.used_at or _expired(record.expires_at):
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    record.used_at = datetime.now(UTC)
    user = db.get(User, record.user_id)
    user.email_verified = True
    db.commit()
    return {"message": "Email verified"}


@router.post("/email/resend", status_code=202)
def resend_email(user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict[str, str]:
    if user.email and not user.email_verified:
        token = secrets.token_urlsafe(32)
        db.add(
            EmailToken(
                user_id=user.id,
                purpose="verify",
                token_hash=hash_token(token),
                expires_at=datetime.now(UTC) + timedelta(hours=24),
            )
        )
        db.commit()
        get_email_sender(get_settings()).send(user.email, "Verify your email", f"Use this token: {token}")
    return {"message": "If applicable, a verification email was sent"}


@router.post("/password/forgot", status_code=202)
def forgot_password(payload: EmailRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    user = db.scalar(select(User).where(User.email == _email(str(payload.email)), User.deleted_at.is_(None)))
    if user and user.email:
        token = secrets.token_urlsafe(32)
        db.add(
            EmailToken(
                user_id=user.id,
                purpose="reset",
                token_hash=hash_token(token),
                expires_at=datetime.now(UTC) + timedelta(minutes=30),
            )
        )
        db.commit()
        get_email_sender(get_settings()).send(user.email, "Reset your password", f"Use this token: {token}")
    return {"message": "If an account exists, a reset email was sent"}


@router.post("/password/reset")
def reset_password(payload: PasswordResetRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    record = db.scalar(select(EmailToken).where(EmailToken.token_hash == hash_token(payload.token)))
    if not record or record.purpose != "reset" or record.used_at or _expired(record.expires_at):
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    user = db.get(User, record.user_id)
    user.password_hash = hash_password(payload.new_password)
    record.used_at = datetime.now(UTC)
    db.query(RefreshToken).filter(RefreshToken.user_id == user.id).update(
        {RefreshToken.revoked_at: datetime.now(UTC)}, synchronize_session=False
    )
    db.commit()
    return {"message": "Password reset"}


@router.post("/password/change")
def change_password(
    payload: PasswordChangeRequest, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> dict[str, str]:
    if user.password_hash and not verify_password(payload.current_password or "", user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    user.password_hash = hash_password(payload.new_password)
    db.commit()
    return {"message": "Password changed"}
