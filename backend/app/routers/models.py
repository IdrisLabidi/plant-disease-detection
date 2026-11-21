from fastapi import APIRouter, Request

router = APIRouter(prefix="/models", tags=["models"])


@router.get("")
def list_models(request: Request) -> dict[str, list[dict]]:
    registry = getattr(request.app.state, "model_registry", None)
    if not registry:
        return {"models": []}
    items = []
    for name in ("resnet50", "mobilenet"):
        card = registry.get_card(name)
        if card:
            items.append(
                {
                    "name": name,
                    "version": card.version,
                    "sha256": card.file_hash,
                }
            )
    return {"models": items}
