from fastapi import APIRouter, Request

router = APIRouter(tags=["health"])


@router.get("/health")
def health(request: Request) -> dict:
    registry = getattr(request.app.state, "model_registry", None)
    return {"status": "ok", "models_loaded": bool(registry and registry.is_loaded())}
