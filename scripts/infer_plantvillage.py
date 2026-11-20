#!/usr/bin/env python3
"""Infer a PlantVillage crop/disease class with MobileNetV3 or ResNet-50 exports."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from PIL import Image, ImageDraw


DEFAULT_MEAN = [0.485, 0.456, 0.406]
DEFAULT_STD = [0.229, 0.224, 0.225]
DEFAULT_INPUT_SIZE = [224, 224]


def load_config(model_path: Path, config_path: Path | None) -> dict:
    """Load export metadata when it is next to the model or explicitly supplied."""
    path = config_path or model_path.with_name("model_config.json")
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def load_checkpoint(path: Path, device: torch.device) -> dict:
    """Load a local PyTorch checkpoint, including both export formats used by the notebook."""
    try:
        return torch.load(path, map_location=device, weights_only=True)
    except TypeError:
        return torch.load(path, map_location=device)
    except Exception:
        # Notebook checkpoints contain tensors and metadata only. This fallback supports
        # older PyTorch versions that do not accept weights_only.
        return torch.load(path, map_location=device, weights_only=False)


def build_model(backbone: str, num_classes: int) -> nn.Module:
    """Recreate the same classification head used by the Colab notebook."""
    from torchvision.models import (
        MobileNet_V3_Large_Weights,
        ResNet50_Weights,
        mobilenet_v3_large,
        resnet50,
    )

    if backbone == "mobilenet_v3":
        model = mobilenet_v3_large(weights=None)
        model.classifier[-1] = nn.Linear(
            model.classifier[-1].in_features, num_classes
        )
    elif backbone == "resnet50":
        model = resnet50(weights=None)
        model.fc = nn.Linear(model.fc.in_features, num_classes)
    else:
        raise ValueError(
            f"Unsupported backbone {backbone!r}; use mobilenet_v3 or resnet50"
        )
    return model


def preprocess(image: Image.Image, config: dict) -> torch.Tensor:
    """Resize, scale, and normalize an RGB image exactly like training."""
    input_size = config.get("input_size", DEFAULT_INPUT_SIZE)
    if (
        not isinstance(input_size, list)
        or len(input_size) != 2
        or any(not isinstance(value, int) or value <= 0 for value in input_size)
    ):
        raise ValueError(
            f"input_size must contain two positive integers, got {input_size!r}"
        )

    resized = image.resize(
        (input_size[1], input_size[0]),
        Image.Resampling.BILINEAR,
    )
    array = np.asarray(resized, dtype=np.float32) / 255.0
    tensor = torch.from_numpy(array).permute(2, 0, 1)

    mean = torch.tensor(
        config.get("normalization_mean", DEFAULT_MEAN),
        dtype=torch.float32,
    ).view(3, 1, 1)
    std = torch.tensor(
        config.get("normalization_std", DEFAULT_STD),
        dtype=torch.float32,
    ).view(3, 1, 1)
    if mean.shape != (3, 1, 1) or std.shape != (3, 1, 1) or torch.any(std <= 0):
        raise ValueError(
            "normalization_mean and normalization_std must each contain "
            "three positive values"
        )
    return ((tensor - mean) / std).unsqueeze(0)


def load_classifier(
    model_path: Path,
    config: dict,
    backbone: str,
    device: torch.device,
) -> torch.nn.Module:
    """Load either a TorchScript export or a PyTorch checkpoint."""
    suffix = model_path.suffix.lower()
    if suffix == ".ts":
        model = torch.jit.load(str(model_path), map_location=device)
        return model.eval()

    if suffix not in {".pt", ".pth"}:
        raise ValueError("Model must be .ts, .pt, or .pth")

    class_names = config.get("class_names")
    if not isinstance(class_names, list) or not class_names:
        raise ValueError(
            "model_config.json must contain a non-empty class_names list "
            "for PyTorch checkpoint inference"
        )

    model = build_model(backbone, len(class_names))
    loaded = load_checkpoint(model_path, device)

    # Notebook best.pt/latest.pt are checkpoint dictionaries; state_dict.pt is
    # the raw model state dictionary.
    state_dict = loaded.get("model") if isinstance(loaded, dict) and "model" in loaded else loaded
    model.load_state_dict(state_dict)
    return model.to(device).eval()


def draw_prediction(image: Image.Image, top_predictions: list[dict]) -> Image.Image:
    """Draw the top predicted class and confidence over a copy of the image."""
    annotated = image.copy()
    draw = ImageDraw.Draw(annotated)
    top = top_predictions[0]
    text = f"{top['class']}: {top['confidence']:.2%}"
    box = draw.textbbox((12, 12), text)
    draw.rectangle(
        (8, 8, box[2] + 4, box[3] + 4),
        fill=(0, 0, 0),
    )
    draw.text((12, 12), text, fill=(255, 255, 255))
    return annotated


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model",
        type=Path,
        required=True,
        help="PlantVillage .ts, .pt, or .pth model",
    )
    parser.add_argument("--image", type=Path, required=True, help="Plant photo")
    parser.add_argument(
        "--config",
        type=Path,
        help="Optional model_config.json (defaults beside --model)",
    )
    parser.add_argument(
        "--backbone",
        choices=("auto", "mobilenet_v3", "resnet50"),
        default="auto",
        help="Required for .pt/.pth unless model_config.json declares it",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of predictions to include",
    )
    parser.add_argument(
        "--device",
        choices=("auto", "cpu", "cuda"),
        default="auto",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("classifier_output"),
        help="Directory for JSON and optional annotated image",
    )
    args = parser.parse_args()

    if not 1 <= args.top_k <= 100:
        parser.error("--top-k must be between 1 and 100")
    if not args.model.is_file():
        parser.error(f"Model does not exist: {args.model}")
    if not args.image.is_file():
        parser.error(f"Image does not exist: {args.image}")
    if args.device == "cuda" and not torch.cuda.is_available():
        parser.error("CUDA was requested but is not available")

    device = torch.device(
        "cuda"
        if args.device == "cuda"
        or (args.device == "auto" and torch.cuda.is_available())
        else "cpu"
    )
    config = load_config(args.model, args.config)
    class_names = config.get("class_names")

    backbone = args.backbone
    if backbone == "auto":
        backbone = config.get("backbone", "mobilenet_v3")
    if backbone not in {"mobilenet_v3", "resnet50"}:
        parser.error(
            "--backbone must be mobilenet_v3 or resnet50, or config must specify one"
        )

    if not isinstance(class_names, list) or not class_names:
        parser.error(
            "No class_names list was found in model_config.json. "
            "Use --config to supply the export metadata."
        )

    image = Image.open(args.image).convert("RGB")
    input_tensor = preprocess(image, config).to(device)
    model = load_classifier(args.model, config, backbone, device)

    # TorchScript and reconstructed checkpoints both expose [batch, class] logits.
    with torch.inference_mode():
        logits = model(input_tensor)
        if isinstance(logits, dict):
            logits = logits.get("out", logits)
        if not isinstance(logits, torch.Tensor) or logits.ndim != 2:
            raise RuntimeError(
                f"Expected classifier logits shaped [batch, classes], "
                f"got {type(logits).__name__} {getattr(logits, 'shape', '')}"
            )
        probabilities = logits.softmax(dim=1)[0].detach().cpu()

    k = min(args.top_k, len(class_names))
    values, indices = torch.topk(probabilities, k=k)
    top_predictions = [
        {
            "class": class_names[index.item()],
            "confidence": float(value.item()),
        }
        for value, index in zip(values, indices)
    ]

    args.output_dir.mkdir(parents=True, exist_ok=True)
    result = {
        "image": str(args.image),
        "model": str(args.model),
        "backbone": backbone,
        "device": str(device),
        "top_predictions": top_predictions,
        "predicted_class": top_predictions[0]["class"],
        "confidence": top_predictions[0]["confidence"],
    }
    json_path = args.output_dir / f"{args.image.stem}_classifier_result.json"
    annotated_path = args.output_dir / f"{args.image.stem}_classifier_overlay.jpg"
    json_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    draw_prediction(image, top_predictions).save(
        annotated_path,
        quality=95,
    )

    print(json.dumps(result, indent=2))
    print(f"JSON: {json_path}")
    print(f"Annotated image: {annotated_path}")


if __name__ == "__main__":
    main()
