import os

try:
    os.unlink("backend-tests.db")
except FileNotFoundError:
    pass

os.environ.setdefault("DATABASE_URL", "sqlite:///./backend-tests.db")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("EMAIL_BACKEND", "console")
os.environ.setdefault("MODELS_DIR", "models")
os.environ.setdefault("STORAGE_DIR", "./backend-tests-storage")

from app import models  # noqa: F401
from app.db import Base, engine

Base.metadata.create_all(bind=engine)
