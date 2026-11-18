#!/usr/bin/env python3
"""Run lesion-segmentation inference with an exported PlantSeg TorchScript model."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch
from PIL import Image


DEFAULT_MEAN = [0.485, 0.456, 0.406]
DEFAULT_STD = [0.229, 0.224, 0.225]


def load_config(model_path: Path, config_path: Path | None) -> dict:
    # Prefer an explicitly supplied config, then look beside the model export.
    path = config_path or model_path.with_name("model_config.json")
    if not path.exists():
        # These values match the notebook export and keep the CLI usable by itself.
        return {
            "input_size": [256, 256],
            "normalization_mean": DEFAULT_MEAN,
            "normalization_std": DEFAULT_STD,
        }
    with path.open(encoding="utf-8") as file:
        config = json.load(file)
    return config


def preprocess(image: Image.Image, config: dict) -> torch.Tensor:
    input_size = config.get("input_size", [256, 256])
    if len(input_size) != 2 or any(not isinstance(value, int) or value <= 0 for value in input_size):
        raise ValueError(f"input_size must contain two positive integers, got {input_size!r}")
    # Match the model's training pipeline: resize, scale pixels to [0, 1],
    # change the image layout from HWC to CHW, and apply ImageNet normalization.
    resized = image.resize((input_size[1], input_size[0]), Image.Resampling.BILINEAR)
    array = np.asarray(resized, dtype=np.float32) / 255.0
    tensor = torch.from_numpy(array).permute(2, 0, 1)
    mean = torch.tensor(config.get("normalization_mean", DEFAULT_MEAN), dtype=torch.float32).view(3, 1, 1)
    std = torch.tensor(config.get("normalization_std", DEFAULT_STD), dtype=torch.float32).view(3, 1, 1)
    if mean.shape != (3, 1, 1) or std.shape != (3, 1, 1) or torch.any(std <= 0):
        raise ValueError("normalization_mean and normalization_std must each contain three valid values")
    return ((tensor - mean) / std).unsqueeze(0)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, required=True, help="Path to plantseg_lesion_segmentation.ts")
    parser.add_argument("--image", type=Path, required=True, help="Input plant image")
    parser.add_argument("--output-dir", type=Path, default=Path("inference_output"))
    parser.add_argument("--config", type=Path, help="Optional model_config.json")
    parser.add_argument("--threshold", type=float, default=0.5, help="Lesion probability threshold")
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    args = parser.parse_args()

    if not 0.0 <= args.threshold <= 1.0:
        parser.error("--threshold must be between 0 and 1")
    if not args.model.is_file():
        parser.error(f"Model does not exist: {args.model}")
    if not args.image.is_file():
        parser.error(f"Image does not exist: {args.image}")
    # "auto" uses the GPU when available; explicit CUDA requests fail clearly.
    if args.device == "cuda" and not torch.cuda.is_available():
        parser.error("CUDA was requested but is not available")

    device = torch.device(
        "cuda" if args.device == "cuda" or (args.device == "auto" and torch.cuda.is_available()) else "cpu"
    )
    config = load_config(args.model, args.config)
    image = Image.open(args.image).convert("RGB")
    input_tensor = preprocess(image, config).to(device)
    model = torch.jit.load(str(args.model), map_location=device).eval()

    # The exported model returns two logits per pixel: background and lesion.
    with torch.inference_mode():
        output = model(input_tensor)
    if not isinstance(output, torch.Tensor) or output.ndim != 4 or output.shape[0] != 1 or output.shape[1] < 2:
        raise RuntimeError(f"Expected model output shaped [1, >=2, H, W], got {type(output).__name__} {getattr(output, 'shape', '')}")

    # Convert lesion logits to probabilities and restore the original image size.
    probability = output.softmax(dim=1)[:, 1]
    probability_image = Image.fromarray((probability[0].cpu().numpy() * 255).astype(np.uint8))
    probability_image = probability_image.resize(image.size, Image.Resampling.BILINEAR)
    probability_array = np.asarray(probability_image, dtype=np.float32) / 255.0
    # Thresholding produces a displayable binary mask (0 = background, 255 = lesion).
    mask_array = (probability_array >= args.threshold).astype(np.uint8) * 255

    args.output_dir.mkdir(parents=True, exist_ok=True)
    mask_path = args.output_dir / f"{args.image.stem}_mask.png"
    overlay_path = args.output_dir / f"{args.image.stem}_overlay.png"
    summary_path = args.output_dir / f"{args.image.stem}_result.json"
    Image.fromarray(mask_array, mode="L").save(mask_path)

    # Blend detected pixels in red over the original image for quick visual inspection.
    base = np.asarray(image, dtype=np.float32)
    red = np.zeros_like(base)
    red[..., 0] = 255
    alpha = (mask_array > 0)[..., None] * 0.45
    overlay = (base * (1 - alpha) + red * alpha).clip(0, 255).astype(np.uint8)
    Image.fromarray(overlay).save(overlay_path)

    summary = {
        "image": str(args.image),
        "model": str(args.model),
        "device": str(device),
        "threshold": args.threshold,
        "lesion_area_fraction": float((mask_array > 0).mean()),
        "mask": str(mask_path),
        "overlay": str(overlay_path),
    }
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
