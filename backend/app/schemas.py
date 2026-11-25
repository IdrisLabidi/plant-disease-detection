import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr | None
    email_verified: bool
    display_name: str | None
    created_at: datetime


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10)
    display_name: str | None = Field(default=None, max_length=120)

    @field_validator("password")
    @classmethod
    def password_not_common(cls, value: str) -> str:
        if value.lower() in {"password123", "password1234", "1234567890", "qwertyuiop"}:
            raise ValueError("password is too common")
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class EmailRequest(BaseModel):
    email: EmailStr


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse
    is_new_user: bool | None = None


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=20)


class TokenRequest(BaseModel):
    token: str = Field(min_length=20)


class PasswordResetRequest(BaseModel):
    token: str = Field(min_length=20)
    new_password: str = Field(min_length=10)


class PasswordChangeRequest(BaseModel):
    current_password: str | None = None
    new_password: str = Field(min_length=10)


class MeUpdateRequest(BaseModel):
    display_name: str | None = Field(default=None, max_length=120)


class GoogleLoginRequest(BaseModel):
    id_token: str = Field(min_length=20)
    nonce: str | None = None


class FacebookLoginRequest(BaseModel):
    access_token: str = Field(min_length=20)


class TopPrediction(BaseModel):
    class_name: str
    probability: float = Field(ge=0, le=1)


class ScanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    client_id: str | None
    created_at: datetime
    source: str
    model_name: str
    model_version: str
    top_class: str
    confidence: float
    top3: list[TopPrediction] | list[Any]
    unsure: bool
    lesion_area_frac: float | None
    mask_url: str | None = None
    image_url: str | None = None
    latency_ms: int | None
    notes: str | None


class IngestRequest(BaseModel):
    client_id: str = Field(min_length=1, max_length=255)
    result: dict[str, Any]
    model_name: str
    model_version: str


class DeleteAccountRequest(BaseModel):
    current_password: str | None = None
    provider: str | None = None
    provider_token: str | None = None
