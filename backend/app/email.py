from typing import Protocol

from .config import Settings


class EmailSender(Protocol):
    def send(self, recipient: str, subject: str, body: str) -> None: ...


class ConsoleEmailSender:
    def send(self, recipient: str, subject: str, body: str) -> None:
        print(f"Email to {recipient}: {subject}\n{body}")


def get_email_sender(settings: Settings) -> EmailSender:
    if settings.email_backend == "console":
        return ConsoleEmailSender()
    raise RuntimeError("SMTP email backend is not configured yet")
