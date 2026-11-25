import base64
import json
import time
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..db import get_db
from ..deps import current_user
from ..ml.pipeline import classify
from ..ml.pipeline import segment as run_segment
from ..ml.preprocess import normalize_image, sanitize_image
from ..models import Scan, User
from ..schemas import ScanResponse
from ..storage import LocalScanStorage

router = APIRouter(prefix="/scans", tags=["scans"])


def _storage(request: Request) -> LocalScanStorage:
    storage = getattr(request.app.state, "storage", None)
    if storage is None:
        storage = LocalScanStorage(get_settings().storage_dir)
        request.app.state.storage = storage
    return storage


def _scan_response(scan: Scan) -> dict:
    return {
        "id": scan.id,
        "client_id": scan.client_id,
        "created_at": scan.created_at,
        "source": scan.source,
        "model_name": scan.model_name,
        "model_version": scan.model_version,
        "top_class": scan.top_class,
        "confidence": scan.confidence,
        "top3": scan.top3,
        "unsure": scan.unsure,
        "lesion_area_frac": scan.lesion_area_frac,
        "mask_url": f"/scans/{scan.id}/mask" if scan.mask_path else None,
        "latency_ms": scan.latency_ms,
        "notes": scan.notes,
    }


def _owned_scan(db: Session, scan_id: uuid.UUID, user: User) -> Scan:
    scan = db.scalar(select(Scan).where(Scan.id == scan_id, Scan.user_id == user.id))
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan


@router.post("", response_model=ScanResponse)
def create_scan(
    request: Request,
    file: UploadFile = File(...),
    model: str = Form(...),
    segment: bool = Form(False),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    if model not in {"resnet50", "mobilenet"}:
        raise HTTPException(status_code=422, detail="Unknown model")
    content = file.file.read(get_settings().max_upload_mb * 1024 * 1024 + 1)
    if len(content) > get_settings().max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Image too large")
    if file.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(status_code=415, detail="Unsupported image type")
    try:
        sanitized, _ = sanitize_image(content)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image") from None

    registry = getattr(request.app.state, "model_registry", None)
    if not registry or model not in registry.classifiers:
        raise HTTPException(status_code=503, detail="Model is unavailable")
    card = registry.get_card(model)
    if not card:
        raise HTTPException(status_code=503, detail="Model card is unavailable")

    started = time.perf_counter()
    tensor = normalize_image(sanitized, card.input_size, card.mean, card.std)
    with registry.semaphore:
        top3, unsure = classify(registry.classifiers[model], card, tensor)
    top_class = top3[0]["class_name"]
    confidence = top3[0]["probability"]

    lesion_area_frac = None
    mask_path = None
    if segment:
        segmenter_key = (
            model if model in registry.segmenters else next(iter(registry.segmenters), None)
        )
        if not segmenter_key:
            raise HTTPException(status_code=503, detail="Segmenter is unavailable")
        seg_card = registry.get_card(segmenter_key, True)
        if not seg_card:
            raise HTTPException(status_code=503, detail="Segmenter card is unavailable")
        seg_tensor = normalize_image(sanitized, seg_card.input_size, seg_card.mean, seg_card.std)
        with registry.semaphore:
            lesion_area_frac, mask_image = run_segment(
                registry.segmenters[segmenter_key], seg_card, seg_tensor
            )
        mask_bytes = b""
        import io

        output = io.BytesIO()
        mask_image.save(output, format="PNG")
        mask_bytes = output.getvalue()
        mask_path = _storage(request).save(
            f"{user.id}/{uuid.uuid4()}.png",
            mask_bytes,
        )

    latency_ms = round((time.perf_counter() - started) * 1000)
    image_path = _storage(request).save(
        f"{user.id}/{uuid.uuid4()}.jpg",
        sanitized,
    )
    scan = Scan(
        user_id=user.id,
        client_id=None,
        source="server",
        model_name=model,
        model_version=card.version,
        top_class=top_class,
        confidence=confidence,
        top3=top3,
        unsure=unsure,
        lesion_area_frac=lesion_area_frac,
        image_path=image_path,
        mask_path=mask_path,
        latency_ms=latency_ms,
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)
    return _scan_response(scan)


@router.post("/ingest", response_model=ScanResponse)
async def ingest_scan(
    request: Request,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        payload = await request.json()
        client_id = payload.get("client_id")
        result = payload.get("result")
        model_name = payload.get("model_name")
        model_version = payload.get("model_version")
        notes = payload.get("notes")
        image_content = None
    else:
        form = await request.form()
        client_id = form.get("client_id")
        model_name = form.get("model_name")
        model_version = form.get("model_version")
        notes = form.get("notes")
        try:
            result = json.loads(str(form.get("result", "{}")))
        except json.JSONDecodeError:
            raise HTTPException(status_code=422, detail="Invalid result JSON") from None
        upload = form.get("image")
        image_content = await upload.read() if hasattr(upload, "read") else None

    if not isinstance(client_id, str) or not client_id:
        raise HTTPException(status_code=422, detail="client_id is required")
    if model_name not in {"resnet50", "mobilenet"}:
        raise HTTPException(status_code=422, detail="Unknown model")
    if not isinstance(result, dict):
        raise HTTPException(status_code=422, detail="Invalid result")

    existing = db.scalar(select(Scan).where(Scan.user_id == user.id, Scan.client_id == client_id))
    if existing:
        return _scan_response(existing)

    top3 = result.get("top3")
    top_class = result.get("top_class")
    if not isinstance(top3, list) or not top3:
        raise HTTPException(status_code=422, detail="Invalid top3")
    normalized_top3 = []
    allowed = None
    registry = getattr(request.app.state, "model_registry", None)
    if registry:
        card = registry.get_card(model_name)
        allowed = card.classes if card else None
    for item in top3:
        if not isinstance(item, dict):
            raise HTTPException(status_code=422, detail="Invalid top3")
        name = item.get("class_name")
        probability = item.get("probability")
        if not isinstance(name, str) or not isinstance(probability, int | float):
            raise HTTPException(status_code=422, detail="Invalid top3")
        probability = float(probability)
        if probability < 0 or probability > 1:
            raise HTTPException(status_code=422, detail="Invalid probability")
        if allowed and name not in allowed:
            raise HTTPException(status_code=422, detail="Unknown class name")
        normalized_top3.append({"class_name": name, "probability": probability})
    top_class = top_class or normalized_top3[0]["class_name"]
    confidence = normalized_top3[0]["probability"]
    if top_class not in {item["class_name"] for item in normalized_top3}:
        raise HTTPException(status_code=422, detail="Invalid top_class")

    unsure = bool(result.get("unsure", False))
    lesion = result.get("lesion_area_frac")
    if lesion is not None:
        lesion = float(lesion)
        if lesion < 0 or lesion > 1:
            raise HTTPException(status_code=422, detail="Invalid lesion_area_frac")

    image_path = None
    if image_content:
        try:
            image_content, _ = sanitize_image(image_content)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid image") from None
        image_path = _storage(request).save(f"{user.id}/{uuid.uuid4()}.jpg", image_content)

    scan = Scan(
        user_id=user.id,
        client_id=client_id,
        source="device",
        model_name=model_name,
        model_version=str(model_version or "unknown"),
        top_class=top_class,
        confidence=confidence,
        top3=normalized_top3,
        unsure=unsure,
        lesion_area_frac=lesion,
        image_path=image_path,
        notes=notes,
        latency_ms=result.get("latency_ms"),
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)
    return _scan_response(scan)


def _decode_cursor(cursor: str) -> tuple[datetime, uuid.UUID]:
    raw = base64.urlsafe_b64decode(cursor.encode()).decode()
    created_text, scan_id = raw.split("|", 1)
    return datetime.fromisoformat(created_text), uuid.UUID(scan_id)


def _encode_cursor(scan: Scan) -> str:
    raw = f"{scan.created_at.isoformat()}|{scan.id}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


@router.get("", response_model=dict)
def list_scans(
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
    cursor: str | None = None,
    crop: str | None = None,
    date: str | None = None,
) -> dict:
    query = select(Scan).where(Scan.user_id == user.id)
    if crop:
        query = query.where(Scan.top_class.ilike(f"%{crop}%"))
    if date:
        try:
            day = datetime.fromisoformat(date)
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid date") from None
        query = query.where(Scan.created_at >= day, Scan.created_at < day.replace(hour=23, minute=59, second=59))
    if cursor:
        try:
            created_at, scan_id = _decode_cursor(cursor)
        except Exception:
            raise HTTPException(status_code=422, detail="Invalid cursor") from None
        query = query.where(
            or_(
                Scan.created_at < created_at,
                and_(Scan.created_at == created_at, Scan.id < scan_id),
            )
        )
    rows = db.scalars(query.order_by(Scan.created_at.desc(), Scan.id.desc()).limit(21)).all()
    has_more = len(rows) > 20
    items = rows[:20]
    return {
        "items": [_scan_response(scan) for scan in items],
        "next_cursor": _encode_cursor(items[-1]) if has_more and items else None,
    }


@router.get("/{scan_id}", response_model=ScanResponse)
def get_scan(
    scan_id: uuid.UUID,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    return _scan_response(_owned_scan(db, scan_id, user))


@router.get("/{scan_id}/image")
def get_scan_image(
    scan_id: uuid.UUID,
    request: Request,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    scan = _owned_scan(db, scan_id, user)
    if not scan.image_path:
        raise HTTPException(status_code=404, detail="Image not found")
    try:
        _storage(request).read(scan.image_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Image not found") from None
    return FileResponse(scan.image_path)


@router.get("/{scan_id}/mask")
def get_scan_mask(
    scan_id: uuid.UUID,
    request: Request,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    scan = _owned_scan(db, scan_id, user)
    if not scan.mask_path:
        raise HTTPException(status_code=404, detail="Mask not found")
    try:
        _storage(request).read(scan.mask_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Mask not found") from None
    return FileResponse(scan.mask_path)


@router.delete("/{scan_id}", status_code=204)
def delete_scan(
    scan_id: uuid.UUID,
    request: Request,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    scan = _owned_scan(db, scan_id, user)
    _storage(request).delete(scan.image_path)
    _storage(request).delete(scan.mask_path)
    db.delete(scan)
    db.commit()
