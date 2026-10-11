# Plant Disease Detection App

A web and mobile-friendly app where a user takes a photo of a plant leaf and receives a disease diagnosis, a confidence score, a visual explanation (Grad-CAM heatmap) and treatment and prevention advice.

The core of the project is **fine-tuning pretrained computer vision models** on public plant disease datasets, comparing architectures fairly, and deploying the best one in a lightweight app.

> **Status:** project setup. Crops and classes are not chosen yet (see [`DATA.md`](DATA.md)).

---

## Goals

1. Accurately classify common crop diseases from leaf photos.
2. Make the model work on real field photos, not only clean lab images.
3. Deliver it as a simple, fast app with understandable results.
4. Compare models fairly and document what works and why.

## Core features

- Take or upload a leaf photo
- Top-3 disease predictions with confidence scores
- Grad-CAM heatmap showing the regions the model used
- "Not sure, retake the photo" handling for low confidence or non-leaf images
- Treatment and prevention advice from a curated, referenced knowledge base
- Scan history
- *Stretch:* offline on-device model, multi-language interface

## Models

All models start from pretrained weights and are fine-tuned in two stages (train the new head, then unfreeze the backbone with a low learning rate).

| Model | Role |
|---|---|
| MobileNetV3 / EfficientNet-B0 | Mobile-friendly baseline, on-device candidate |
| ResNet-50 | Reference baseline |
| ConvNeXt-Tiny | Main candidate |
| ViT-B/16 or DINOv2 (with LoRA) | High-accuracy comparison |
| YOLO11 (optional) | Stretch: lesion or leaf localization |

## Tech stack

| Layer | Tools |
|---|---|
| Training | Python, PyTorch, timm, Hugging Face (`transformers`, `datasets`, `peft`), Albumentations |
| Compute | Kaggle notebooks / Google Colab |
| Experiment tracking | Weights & Biases |
| Data and code | GitHub, DVC (or Hugging Face Datasets) |
| Evaluation | scikit-learn, pytorch-grad-cam, FiftyOne |
| Backend | FastAPI, ONNX Runtime, SQLite or PostgreSQL |
| Frontend | React PWA (Flutter / React Native if going native) |
| Deployment | Docker, Hugging Face Spaces or Render |

---

## Repository structure

```
.
├── README.md
├── DATA.md                 # data contract: classes, formats, splits (read this first)
├── requirements.txt
├── configs/
│   ├── classes.yaml        # selected crops and classes (single source of truth)
│   └── train.yaml          # image size, seed, hyperparameters, paths
├── data/                   # NOT in Git (use DVC / Kaggle / Hugging Face)
│   ├── raw/                # immutable, never edited by hand
│   ├── interim/            # after cleaning
│   └── processed/          # final train / val / test
├── src/
│   ├── data/               # download, clean, dedup, split, augment
│   ├── models/             # training, evaluation, export
│   └── app/                # backend API and frontend
├── notebooks/              # exploration only, not part of the pipeline
├── docs/                   # report material, knowledge-base sources
└── tests/                  # data validation and pipeline tests
```

## Getting started

```bash
git clone <repo-url>
cd <repo-name>
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Then:

1. Read [`DATA.md`](DATA.md).
2. Pull the dataset version listed there (instructions to be added once the data remote is set up).
3. Run the shared EDA notebook in `notebooks/`.

Training, evaluation and app run instructions will be added here as each part is built.

---

## How we work

- **`main` is protected.** Nobody pushes directly. Work happens on a branch and is merged through a pull request reviewed by at least one teammate.
- **Branch names:** `data/<topic>`, `model/<topic>`, `eval/<topic>`, `app/<topic>` (e.g. `data/dedup`, `model/convnext`).
- **Keep PRs small**, with a short description of what changed and why. For data changes, say what was removed or changed and how many items (e.g. "dropped 312 near-duplicates").
- **Never commit data or model weights** to Git. Use DVC or the shared remote, and record the dataset version used for each experiment.
- **Notebooks are for exploration.** Anything reusable moves into `src/` as a script.
- **Experiments are logged to the shared W&B project** with descriptive run names, e.g. `convnext_tiny_lr1e-4_aug2`.
- **The test set is untouched** until the final evaluation.
- **Tasks live on the GitHub Projects board**, one issue per task with a clear owner.
- **Sync:** short meeting twice a week plus a shared chat channel.



## Timeline

| Weeks | Milestone |
|---|---|
| 1 | Finalize scope (crops and classes), repo setup, download and explore data |
| 2-3 | Data cleaning, splits, baseline model |
| 4-6 | Fine-tune ConvNeXt and ViT/DINOv2, ablations, lab-to-field experiments |
| 7 | Explainability, confidence handling, export and compression |
| 8-9 | Build backend and frontend, integrate model and knowledge base |
| 10 | Testing, final evaluation, report, demo |

## Evaluation

- Accuracy, macro F1, per-class precision and recall, confusion matrix
- Generalization: train on lab-style data, test on field data, and report the drop
- Efficiency: model size and inference latency (laptop CPU and phone)
- Ablations: frozen vs. full fine-tuning, with and without augmentation, CNN vs. transformer

## Limitations and disclaimer

- The app only recognizes the crops and diseases it was trained on.
- Predictions can be wrong, especially on photos that differ from the training data (lighting, angle, background).
- The app supports decisions and **does not replace an agronomist**.
- Check each dataset's license before use or redistribution (see `DATA.md`).

