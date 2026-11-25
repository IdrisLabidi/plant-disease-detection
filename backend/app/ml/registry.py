import hashlib
import json
import threading
from dataclasses import dataclass
from pathlib import Path

import torch
import yaml


@dataclass
class ModelCard:
    name: str
    version: str
    input_size: tuple[int, int]
    mean: list[float]
    std: list[float]
    classes: list[str]
    softmax_inside_model: bool
    unsure_threshold: float | None
    mask_threshold: float
    file_hash: str


class ModelRegistry:
    def __init__(self, models_dir: str):
        path = Path(models_dir)
        if not path.is_absolute() and not path.exists():
            backend_relative = (Path(__file__).resolve().parents[2] / path).resolve()
            project_relative = (Path(__file__).resolve().parents[3] / path).resolve()
            if backend_relative.exists():
                path = backend_relative
            elif project_relative.exists():
                path = project_relative
        self.models_dir = path.resolve()
        self.cards: dict[str, dict] = {}
        self.classifiers: dict[str, torch.jit.ScriptModule] = {}
        self.segmenters: dict[str, torch.jit.ScriptModule] = {}
        self.metadata: dict[str, ModelCard] = {}
        self.semaphore = threading.BoundedSemaphore(2)

    def load(self) -> None:
        card_file = self.models_dir / "model_cards.yaml"
        if card_file.exists():
            self.cards = yaml.safe_load(card_file.read_text()) or {}

        aliases = {
            "resnet50": ("classifier_resnet50", "segmenter_resnet50"),
            "mobilenet": (
                "classifier_mobilenet_v3",
                "segmenter_mobilenet_v3",
            ),
        }
        for public_name, (classifier_card, segmenter_card) in aliases.items():
            classifier = self.cards.get(classifier_card)
            if classifier:
                model = self._load_public_model(public_name, classifier_card, classifier)
                if model:
                    self.classifiers[public_name] = model
            segmenter = self.cards.get(segmenter_card)
            if segmenter:
                model = self._load_public_model(public_name, segmenter_card, segmenter, segmenter=True)
                if model:
                    self.segmenters[public_name] = model

    def _load_public_model(
        self,
        public_name: str,
        card_name: str,
        card: dict,
        *,
        segmenter: bool = False,
    ):
        candidates = [
            self.models_dir / f"{card_name}.pt",
            self.models_dir / f"{public_name}.pt",
        ]
        if segmenter:
            if public_name == "mobilenet":
                candidates.append(
                    self.models_dir / "deeplabv3-mobilenet" / "plantseg_lesion_segmentation.ts"
                )
        elif public_name == "resnet50":
            candidates.append(
                self.models_dir / "resnet50-classifier" / "plantvillage_classifier.ts"
            )
        path = next((item for item in candidates if item.exists()), None)
        if not path:
            return None

        model = torch.jit.load(str(path), map_location="cpu")
        model.eval()
        input_spec = card["input"]
        size = tuple(input_spec["size"])
        config_file = path.with_name("model_config.json")
        classes: list[str] = []
        if config_file.exists():
            config = json.loads(config_file.read_text())
            classes = config.get("classes") or config.get("class_names") or []
        output = card.get("output", {})
        unsure = card.get("unsure_threshold", {}).get("value")
        mask_threshold = card.get("lesion_threshold", {}).get("value", 0.5)
        metadata = ModelCard(
            name=card_name,
            version=str(card.get("version", "unknown")),
            input_size=(int(size[0]), int(size[1])) if len(size) == 2 else (224, 224),
            mean=list(input_spec["mean"]),
            std=list(input_spec["std"]),
            classes=classes,
            softmax_inside_model=bool(output.get("softmax_inside_model", False)),
            unsure_threshold=float(unsure) if unsure is not None else None,
            mask_threshold=float(mask_threshold),
            file_hash=hashlib.sha256(path.read_bytes()).hexdigest(),
        )
        key = f"{card_name}:classifier" if not segmenter else f"{card_name}:segmenter"
        self.metadata[key] = metadata
        dummy = torch.zeros((1, 3, metadata.input_size[0], metadata.input_size[1]))
        with torch.inference_mode():
            model(dummy)
        return model

    def get_card(self, public_name: str, segmenter: bool = False) -> ModelCard | None:
        card_name = "mobilenet" if public_name == "mobilenet" else "resnet50"
        classifier_key = f"classifier_{card_name}:classifier"
        segmenter_key = f"segmenter_{card_name}:segmenter"
        if public_name == "mobilenet":
            classifier_key = "classifier_mobilenet_v3:classifier"
            segmenter_key = "segmenter_mobilenet_v3:segmenter"
        else:
            classifier_key = "classifier_resnet50:classifier"
            segmenter_key = "segmenter_resnet50:segmenter"
        return self.metadata.get(segmenter_key if segmenter else classifier_key)

    def is_loaded(self) -> bool:
        return bool(self.classifiers)
