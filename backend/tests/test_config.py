from app.config import Settings


def test_cors_origins_accept_comma_separated_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./config.db")
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:8081,https://example.com")

    settings = Settings()

    assert settings.cors_origins == ["http://localhost:8081", "https://example.com"]
