# Models Directory

Model weights (`*.ts`, `*.pt`) and `model_config.json` files are ignored by Git (see `.gitignore`), while `model_cards.yaml` and this `README.md` are tracked so collaborators know how to set up and version models locally.

## Directory Structure

```text
models/
├── README.md
├── model_cards.yaml
├── classifiers/
│   ├── resnet50/
│   │   └── <version>/
│   │       ├── model.ts
│   │       └── model_config.json
│   └── mobilenet/                  # optional
│       └── <version>/
│           ├── model.ts
│           └── model_config.json
└── segmenters/
    ├── mobilenet/
    │   └── <version>/
    │       ├── model.ts
    │       └── model_config.json
    └── resnet50/
        └── <version>/
            ├── model.ts
            └── model_config.json
```

### Naming Rules

- **Task folders:** `classifiers/` and `segmenters/`
- **Model folders:** public API model names (`resnet50`, `mobilenet`)
- **Version folders:** `<version>` (e.g. `2026-11-20`, `v1`, `v2`)
- **Artifacts inside `<version>/`:**
  - `model.ts` (or `model.pt` / `<model_name>.ts` / `<model_name>.pt`) — TorchScript-exported model (`torch.jit.script` or `torch.jit.trace`)
  - `model_config.json` — runtime metadata (`class_names` / `classes`, `input_size`, `normalization_mean`, `normalization_std`)

## Versioning

1. Each model entry in `model_cards.yaml` (`classifier_resnet50`, `classifier_mobilenet_v3`, `segmenter_mobilenet_v3`, `segmenter_resnet50`) specifies a `version` field (for example, `2026-11-20`).
2. `ModelRegistry` (`backend/app/ml/registry.py`) looks for `models/<classifiers|segmenters>/<model_name>/<version>/`.
   - If that exact `<version>` directory exists, it is loaded.
   - If not, it falls back to the latest sorted version directory under `<model_name>/`.
3. To deploy a new version without overwriting the previous one:
   - Export the new TorchScript model and `model_config.json` into a new folder, e.g. `models/classifiers/resnet50/2026-12-01/`.
   - Update `version: 2026-12-01` under `classifier_resnet50` in `models/model_cards.yaml`.
   - Restart the backend (or reload `ModelRegistry`).

## Collaborator Setup

1. Obtain the exported model archive from your team's shared storage (Google Drive / DVC / Kaggle output).
2. Place each exported TorchScript model and its `model_config.json` into the matching `classifiers/<model_name>/<version>/` or `segmenters/<model_name>/<version>/` directory, named `model.ts` and `model_config.json`.
3. Verify the models load before starting the API:
   ```bash
   .venv/bin/python -c "
   from backend.app.ml.registry import ModelRegistry
   r = ModelRegistry('models')
   r.load()
   print('classifiers:', list(r.classifiers.keys()))
   print('segmenters:', list(r.segmenters.keys()))
   "
   ```
4. Start the backend from the project root:
   ```bash
   uv run fastapi dev backend/app/main.py --host 0.0.0.0
   ```
   Check `GET /health` (`"models_loaded": true`) and `GET /models`.
