import io
import json

import torch
import yaml
from PIL import Image

from app.ml.pipeline import classify
from app.ml.preprocess import normalize_image, sanitize_image
from app.ml.registry import ModelRegistry


class DummyClassifier(torch.nn.Module):
    def forward(self, value):
        batch = value.shape[0]
        return torch.ones((batch, 3))


def test_dummy_torchscript_registry_and_preprocess(tmp_path):
    model = torch.jit.trace(DummyClassifier(), torch.zeros((1, 3, 224, 224)))
    model.save(str(tmp_path / "classifier_resnet50.pt"))
    (tmp_path / "model_config.json").write_text(json.dumps({"classes": ["healthy", "rust", "blight"]}))
    (tmp_path / "model_cards.yaml").write_text(
        yaml.safe_dump(
            {
                "classifier_resnet50": {
                    "version": "test",
                    "input": {
                        "size": [224, 224],
                        "mean": [0.485, 0.456, 0.406],
                        "std": [0.229, 0.224, 0.225],
                    },
                    "output": {"softmax_inside_model": False},
                    "unsure_threshold": {"value": 0.1},
                }
            }
        )
    )

    image = Image.new("RGB", (400, 300), "green")
    buffer = io.BytesIO()
    image.save(buffer, "JPEG")
    sanitized, size = sanitize_image(buffer.getvalue())
    assert max(size) <= 2048

    registry = ModelRegistry(str(tmp_path))
    registry.load()
    card = registry.get_card("resnet50")
    assert card is not None
    tensor = normalize_image(sanitized, card.input_size, card.mean, card.std)
    with registry.semaphore:
        top3, unsure = classify(registry.classifiers["resnet50"], card, tensor)
    assert len(top3) == 3
    assert not unsure


class DummySegmenter(torch.nn.Module):
    def forward(self, value):
        batch, _, height, width = value.shape
        return torch.ones((batch, 2, height, width))


def test_versioned_classifiers_and_segmenters_layout(tmp_path):
    cls_dir = tmp_path / "classifiers" / "resnet50" / "v2"
    cls_dir.mkdir(parents=True)
    torch.jit.trace(DummyClassifier(), torch.zeros((1, 3, 224, 224))).save(str(cls_dir / "model.ts"))
    (cls_dir / "model_config.json").write_text(json.dumps({"classes": ["healthy", "rust", "blight"]}))

    # Older version should be ignored when card pins v2
    old_cls_dir = tmp_path / "classifiers" / "resnet50" / "v1"
    old_cls_dir.mkdir(parents=True)
    torch.jit.trace(DummyClassifier(), torch.zeros((1, 3, 224, 224))).save(str(old_cls_dir / "model.ts"))

    seg_dir = tmp_path / "segmenters" / "resnet50" / "2026-11-20"
    seg_dir.mkdir(parents=True)
    torch.jit.trace(DummySegmenter(), torch.zeros((1, 3, 512, 512))).save(str(seg_dir / "model.ts"))
    (seg_dir / "model_config.json").write_text(json.dumps({"input_size": [512, 512]}))

    (tmp_path / "model_cards.yaml").write_text(
        yaml.safe_dump(
            {
                "classifier_resnet50": {
                    "version": "v2",
                    "input": {
                        "size": [224, 224],
                        "mean": [0.485, 0.456, 0.406],
                        "std": [0.229, 0.224, 0.225],
                    },
                    "output": {"softmax_inside_model": False},
                },
                "segmenter_resnet50": {
                    "version": "2026-11-20",
                    "input": {
                        "size": [256, 256],
                        "mean": [0.485, 0.456, 0.406],
                        "std": [0.229, 0.224, 0.225],
                    },
                    "output": {"softmax_inside_model": False},
                },
            }
        )
    )

    registry = ModelRegistry(str(tmp_path))
    registry.load()
    cls_card = registry.get_card("resnet50")
    seg_card = registry.get_card("resnet50", segmenter=True)
    assert cls_card is not None and cls_card.version == "v2"
    assert seg_card is not None and seg_card.version == "2026-11-20"
    assert seg_card.input_size == (512, 512)
