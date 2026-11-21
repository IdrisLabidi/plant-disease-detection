from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ProviderIdentity:
    provider: str
    subject: str
    email: str | None
    email_verified: bool
    name: str | None


class OAuthProvider(Protocol):
    def verify(self, credentials: str, nonce: str | None = None) -> ProviderIdentity: ...
