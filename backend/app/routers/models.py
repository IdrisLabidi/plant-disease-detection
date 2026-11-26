from fastapi import APIRouter, Request

router = APIRouter(prefix="/models", tags=["models"])


@router.get("")
def list_models(request: Request) -> dict[str, list[dict]]:
    registry = getattr(request.app.state, "model_registry", None)
    if not registry:
        return {"models": []}
    items = []
    for task, is_segmenter in (("classifier", False), ("segmenter", True)):
        for name in ("resnet50", "mobilenet"):
            card = registry.get_card(name, segmenter=is_segmenter)
            if card:
                items.append(
                    {
                        "name": name,
                        "task": task,
                        "version": card.version,
                        "sha256": card.file_hash,
                    }
                )
    return {"models": items}
