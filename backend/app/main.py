from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .ml.registry import ModelRegistry
from .routers import auth, health, me, models, oauth, scans
from .storage import LocalScanStorage


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    registry = ModelRegistry(settings.models_dir)
    registry.load()
    _.state.model_registry = registry
    _.state.storage = LocalScanStorage(settings.storage_dir)
    yield


settings = get_settings()
cors_origins = list(settings.cors_origins)
if settings.env != "production":
    for origin in (
        "http://localhost:8081",
        "http://127.0.0.1:8081",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ):
        if origin not in cors_origins:
            cors_origins.append(origin)
app = FastAPI(
    title="Plant Disease Detection API",
    docs_url=None if settings.env == "production" else "/docs",
    redoc_url=None if settings.env == "production" else "/redoc",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(me.router)
app.include_router(oauth.router)
app.include_router(scans.router)
app.include_router(models.router)
