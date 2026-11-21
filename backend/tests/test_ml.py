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
