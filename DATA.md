Data Contract

This file is the single source of truth for how data is stored, formatted, cleaned and split in this project. If you change anything here, do it in a pull request and tell the team.

---

## 1. Scope: crops and classes

**Selected crops:** tomato, apple, corn (maize)

**Why these three:** all three exist in PlantVillage (lab images) and in both field datasets we use, PlantDoc and PlantWild, so we can measure the lab-to-field gap. Together they give 18 classes: a manageable number for error analysis and for writing reviewed treatment advice, with a mix of fungal, bacterial, viral and pest problems. Decision date: _fill in_.

**Class list** (copy of `configs/classes.yaml`, the yaml file is the source of truth). Image counts per source, selected crops only; PlantWild counts are filled in after the folder count:

| ID | Class name (folder name) | PlantVillage (lab) | PlantDoc (field) | PlantWild v2 (field) | Notes |
|---|---|---|---|---|---|
| 0 | apple__apple_scab | 630 | 93 | 258 |  |
| 1 | apple__black_rot | 621 | 0 | 83 | Field images only from PlantWild |
| 2 | apple__cedar_apple_rust | 275 | 89 | 139 | Smallest PlantVillage class (275). PlantWild 'apple rust' assumed cedar apple rust |
| 3 | apple__healthy | 1,645 | 91 | 0 | Field images only from PlantDoc ('Apple leaf', assumed healthy) |
| 4 | corn__gray_leaf_spot | 513 | 68 | 107 |  |
| 5 | corn__common_rust | 1,192 | 116 | 177 | PlantWild 'corn rust' assumed common rust |
| 6 | corn__northern_leaf_blight | 985 | 192 | 130 | PlantDoc 'Corn leaf blight' assumed northern leaf blight |
| 7 | corn__healthy | 1,162 | 0 | 0 | No field images (check PlantWild v1 'corn leaf') |
| 8 | tomato__bacterial_spot | 2,127 | 110 | 110 |  |
| 9 | tomato__early_blight | 1,000 | 88 | 187 |  |
| 10 | tomato__late_blight | 1,909 | 111 | 163 |  |
| 11 | tomato__leaf_mold | 952 | 91 | 156 |  |
| 12 | tomato__septoria_leaf_spot | 1,771 | 151 | 130 |  |
| 13 | tomato__spider_mites | 1,676 | 2 | 0 | Only 2 PlantDoc images: not usable for field evaluation |
| 14 | tomato__target_spot | 1,404 | 0 | 0 | No field images. PlantVillage card mentions a known issue with this class. |
| 15 | tomato__yellow_leaf_curl_virus | 5,357 | 76 | 93 | Largest class (5,357): watch imbalance |
| 16 | tomato__mosaic_virus | 373 | 54 | 63 | Small PlantVillage class (373) |
| 17 | tomato__healthy | 1,591 | 63 | 0 | Field images only from PlantDoc ('Tomato leaf', assumed healthy) |
| | **Total** | **25,183** | **1,395** | 1640 | |

The source label strings for every class are in `configs/mappings/plantvillage.yaml`, `plantdoc.yaml` and `plantwild.yaml`.

Rules:

- Class names are lowercase, use underscores, and follow `crop__condition`. Two underscores separate crop from condition.
- Every crop has a `healthy` class.
- The order of classes in `configs/classes.yaml` defines the numeric IDs. Never reorder them after training starts.
- All code reads the class list from `configs/classes.yaml`. **Do not hard-code class names.**

Known data issues to handle:

- **Crop imbalance:** tomato has 18,160 of 25,183 PlantVillage images (72%), corn 3,852 (15%), apple 3,171 (13%). The largest class (5,357) is about 19 times the smallest (275). Report macro F1 and per-crop results, and use class weights or sampling.
- **Field coverage (PlantDoc + PlantWild v2):** 15 of 18 classes have usable field images. `corn__healthy` and `tomato__target_spot` have none, and `tomato__spider_mites` has only 2 (PlantDoc). Healthy field images exist only for apple and tomato, from PlantDoc, with assumed labels. Report this coverage explicitly.
- **PlantWild v2 has no healthy classes and no split metadata.** We create our own split (section 6). Check PlantWild v1 (`<plant> leaf` folders) for healthy images.
- **Possible overlap between field datasets:** PlantDoc and PlantWild are both web-collected. Run a cross-dataset near-duplicate check before building any field split.
- **Assumed labels:** PlantDoc "Apple leaf", "Tomato leaf", "Corn leaf blight" and PlantWild "apple rust", "corn rust" are mapped by assumption. Check sample images before trusting them.
- **PlantWild license:** CC BY-NC-ND 4.0. Keep the images private (no public Hugging Face, Roboflow or data-remote copies) and share only scripts and split files.
- **Tomato target spot:** the PlantVillage dataset card mentions a known issue with this class.

---

## 2. Source datasets

Verify the current link, license and class list for each source before downloading, and fill in the table.

| Dataset | Type | Used for | Link | License | Downloaded | Notes |
|---|---|---|---|---|---|---|
| PlantVillage | Lab-style, plain backgrounds | Main training data, baseline |[link](https://huggingface.co/datasets/geraldmc/plantvillage-full)|CC0 1.0| no | Some copies contain pre-augmented duplicates |
| PlantDoc | Field images, has bounding boxes | Field fine-tuning and testing |[link](https://huggingface.co/datasets/geraldmc/plantdoc-full)| CC BY 4.0| no | Small, labels may be noisy |
| PlantWild | Field images | Extra real-world data, robustness | [link](https://tqwei05.github.io/PlantWild/) | [Creative Commons BY-NC-ND 4.0 license.](https://creativecommons.org/licenses/by-nc-nd/4.0/) | yes | |
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