Data Contract

This file is the single source of truth for how data is stored, formatted, cleaned and split in this project. If you change anything here, do it in a pull request and tell the team.

> **Status:** draft. Crop and class selection is **not decided yet** (see section 1).

---

## 1. Scope: crops and classes

**Selected crops:** _TBD_

**Class list:** _TBD_ (the final list lives in `configs/classes.yaml`; this table is a readable copy)

| ID | Crop | Condition | Class name (folder name) | Notes |
|---|---|---|---|---|
| 0 | | | | |
| 1 | | | | |
| 2 | | | | |

Rules:

- Class names are lowercase, use underscores, and follow `crop__condition`, e.g. `cropname__diseasename` and `cropname__healthy`. Two underscores separate crop from condition.
- Every crop includes a `healthy` class.
- The order of classes in `configs/classes.yaml` defines the numeric IDs. Never reorder them after training starts.
- All code reads the class list from `configs/classes.yaml`. **Do not hard-code class names.**

Example `configs/classes.yaml` (to fill in once the choice is made):

```yaml
crops: []        # e.g. [cropA, cropB, cropC]
classes: []      # e.g. [cropA__healthy, cropA__diseaseX, ...]
```

Selection criteria to decide with the team:

- Crops present in **both** a lab-style dataset and at least one field dataset, so we can measure the lab-to-field gap.
- Enough images per class (see section 3).
- We can write reliable treatment advice for each disease.

---

## 2. Source datasets

Verify the current link, license and class list for each source before downloading, and fill in the table.

| Dataset | Type | Used for | Link | License | Downloaded | Notes |
|---|---|---|---|---|---|---|
| PlantVillage | Lab-style, plain backgrounds | Main training data, baseline | _TBD_ | _TBD_ | no | Some copies contain pre-augmented duplicates |
| PlantDoc | Field images, has bounding boxes | Field fine-tuning and testing | _TBD_ | _TBD_ | no | Small, labels may be noisy |
| PlantWild | Field images | Extra real-world data, robustness | _TBD_ | _TBD_ | no | |
| Cassava Leaf Disease | Field images | Out-of-domain test | _TBD_ | _TBD_ | no | Only relevant if cassava is selected |
| _other_ | | | | | | |

Rules:

- Original downloads go to `data/raw/<dataset_name>/` and are **never edited**.
- Record the source URL, download date and license for every dataset in the table above.
- Do not mix datasets into one folder until class names are mapped to our class list (section 4).

---

## 3. Folder layout

```
data/
├── raw/
│   ├── plantvillage/            # untouched original download
│   ├── plantdoc/
│   └── .../
├── interim/                     # after cleaning, before splitting
│   └── <class_name>/xxxx.jpg
├── processed/
│   ├── v1/
│   │   ├── train/<class_name>/xxxx.jpg
│   │   ├── val/<class_name>/xxxx.jpg
│   │   └── test/<class_name>/xxxx.jpg
│   └── v2/ ...                  # new version after further cleaning
└── splits/
    └── v1_split.csv             # image_id, source, class, split
```

The `train/<class_name>/image.jpg` layout works directly with PyTorch `ImageFolder` and Hugging Face `datasets`.

Minimum target per class (adjust after EDA): at least ~200 images in total, and at least ~30 in each of val and test. Classes below this are merged, dropped or flagged.

---

## 4. Format conventions

| Item | Convention |
|---|---|
| Image format | JPEG (`.jpg`), RGB, 3 channels. Convert PNG or other formats during cleaning. |
| Training resolution | 224 x 224 (configurable in `configs/train.yaml`). Raw images are kept at original size. |
| File names | `<source>_<original_id>.jpg`, e.g. `plantvillage_000123.jpg`. Must be unique across the project. |
| Label source | Folder name = class name from `configs/classes.yaml`. |
| Normalization | ImageNet mean and std (`[0.485, 0.456, 0.406]`, `[0.229, 0.224, 0.225]`) unless a model requires otherwise. |
| Detection labels (optional) | YOLO `.txt` format, one file per image, only if we do the YOLO stretch goal. |

### Mapping source labels to our classes

Each source dataset names classes differently. For every dataset, write a mapping file `configs/mappings/<dataset>.yaml` from source label to our class name. Source labels with no match are **excluded**, not guessed.

---

## 5. Cleaning rules

Applied in order by scripts in `src/data/`. Each step logs how many images it removed.

1. **Corrupt or unreadable files:** remove.
2. **Tiny or near-blank images:** remove if the shorter side is under 64 px, or if the image is almost a single color.
3. **Exact duplicates:** remove (file hash).
4. **Near-duplicates:** remove or group using perceptual hashing (`imagehash`) or embedding similarity. This matters especially for PlantVillage, where many images show the same leaf from slightly different angles.
5. **Not a leaf / wrong crop:** flag with a quick model or manual review (FiftyOne), then remove.
6. **Label audit:** review suspicious labels (high-confidence mistakes from a quick baseline) with cleanlab or FiftyOne. Record every label fix in the changelog.
7. **Class mapping and class balance check:** apply mappings, then report counts per class and per source.

---

## 6. Splits

- **Ratios:** 70 / 15 / 15 (train / val / test), adjustable after EDA.
- **Random seed:** `42`. Fixed for all splits.
- **Split once, commit the result.** The split is stored in `data/splits/vN_split.csv` and committed to Git. Everyone uses the same file.
- **Stratified** by class so every split has all classes.
- **Group-aware where possible:** near-duplicate groups and images of the same leaf or plant must stay in the **same** split.
- **Order of operations:** clean, deduplicate, **split**, then augment. **Never augment before splitting**, and augmentation is applied to the training set only.
- **Field test set (planned):** a separate test set made only of real-world field images, reported separately from the lab-style test set, so we can measure the lab-to-field gap.
- **The test sets are not used** for tuning or model selection until the final evaluation.

---

## 7. Augmentation (training only)

Defined in `configs/train.yaml` and applied on the fly. Planned operations: random resized crop, flip, rotation, color jitter, blur, random background or lighting changes (to reduce the lab-to-field gap). Augmented images are **not saved** into `data/processed/`.

---

## 8. Versioning

- Each cleaned dataset release is a version: `v1`, `v2`, ...
- Data is versioned with DVC (or a private Hugging Face / Kaggle dataset), **not** stored in Git.
- Every experiment records the dataset version it used (W&B config field `data_version`).
- A new version is created whenever images, labels or splits change. Describe what changed in the changelog below.

---

## 9. Validation checks (run in CI)

Automated tests in `tests/` should confirm that:

- every image opens and is RGB
- every image's class exists in `configs/classes.yaml`
- no image ID appears in more than one split
- every class appears in train, val and test
- no near-duplicate group crosses splits

---

## 10. Licensing and privacy

- Respect each dataset's license, and keep attribution in the table in section 2.
- Photos we collect ourselves: record who took them, when, and make sure the photographer agrees to their use. Remove location metadata (EXIF GPS) before sharing.
- Do not redistribute datasets whose license forbids it. Share only scripts and split files in those cases.

---

## 11. Changelog

| Version | Date | Author | Changes |
|---|---|---|---|
| draft | _TBD_ | _TBD_ | Initial template, no data downloaded yet |