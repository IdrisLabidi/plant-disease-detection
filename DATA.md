Data Contract

This file is the single source of truth for how data is stored, formatted, cleaned and split in this project. If you change anything here, do it in a pull request and tell the team.

> **Status:** draft. Crop and class selection is **not decided yet** (see section 1).

---

## 1. Scope: crops and classes

**Selected crops:** tomato, apple, corn (maize)

**Why these three:** all three exist in both PlantVillage (lab images) and PlantDoc (field images), so we can measure the lab-to-field gap. Together they give 18 classes: a manageable number for error analysis and for writing reviewed treatment advice, with a mix of fungal, bacterial, viral and pest problems. Decision date: _fill in_.

**Class list** (copy of `configs/classes.yaml`; the yaml file is the source of truth). Counts come from the EDA of `geraldmc/plantvillage-full` and `geraldmc/plantdoc-full` (selected crops only):

| ID | Crop | Class name (folder name) | PlantVillage label | PV images | PlantDoc label | PlantDoc images | Notes |
|---|---|---|---|---|---|---|---|
| 0 | apple | apple__apple_scab | Apple___Apple_scab | 630 | Apple Scab Leaf | 93 |  |
| 1 | apple | apple__black_rot | Apple___Black_rot | 621 | - | 0 | No field images |
| 2 | apple | apple__cedar_apple_rust | Apple___Cedar_apple_rust | 275 | Apple rust leaf | 89 | Smallest PlantVillage class (275) |
| 3 | apple | apple__healthy | Apple___healthy | 1,645 | Apple leaf | 91 | PlantDoc 'Apple leaf' assumed healthy |
| 4 | corn | corn__gray_leaf_spot | Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot | 513 | Corn Gray leaf spot | 68 |  |
| 5 | corn | corn__common_rust | Corn_(maize)___Common_rust_ | 1,192 | Corn rust leaf | 116 |  |
| 6 | corn | corn__northern_leaf_blight | Corn_(maize)___Northern_Leaf_Blight | 985 | Corn leaf blight | 192 | PlantDoc 'Corn leaf blight' assumed northern leaf blight |
| 7 | corn | corn__healthy | Corn_(maize)___healthy | 1,162 | - | 0 | No field images |
| 8 | tomato | tomato__bacterial_spot | Tomato___Bacterial_spot | 2,127 | Tomato leaf bacterial spot | 110 |  |
| 9 | tomato | tomato__early_blight | Tomato___Early_blight | 1,000 | Tomato Early blight leaf | 88 |  |
| 10 | tomato | tomato__late_blight | Tomato___Late_blight | 1,909 | Tomato leaf late blight | 111 |  |
| 11 | tomato | tomato__leaf_mold | Tomato___Leaf_Mold | 952 | Tomato mold leaf | 91 |  |
| 12 | tomato | tomato__septoria_leaf_spot | Tomato___Septoria_leaf_spot | 1,771 | Tomato Septoria leaf spot | 151 |  |
| 13 | tomato | tomato__spider_mites | Tomato___Spider_mites Two-spotted_spider_mite | 1,676 | Tomato two spotted spider mites leaf | 2 | Only 2 field images: not usable for field evaluation |
| 14 | tomato | tomato__target_spot | Tomato___Target_Spot | 1,404 | - | 0 | Dataset card mentions a known issue; check before use. No field images. |
| 15 | tomato | tomato__yellow_leaf_curl_virus | Tomato___Tomato_Yellow_Leaf_Curl_Virus | 5,357 | Tomato leaf yellow virus | 76 | Largest class (5,357): watch imbalance |
| 16 | tomato | tomato__mosaic_virus | Tomato___Tomato_mosaic_virus | 373 | Tomato leaf mosaic virus | 54 | Small class (373); only 54 field images |
| 17 | tomato | tomato__healthy | Tomato___healthy | 1,591 | Tomato leaf | 63 | PlantDoc 'Tomato leaf' assumed healthy |
| | | **Total** | | **25,183** | | **1,395** | 18 classes in PlantVillage, 15 in PlantDoc |

Label mappings: `configs/mappings/plantvillage.yaml` and `configs/mappings/plantdoc.yaml`.

Rules:

- Class names are lowercase, use underscores, and follow `crop__condition`. Two underscores separate crop from condition.
- Every crop has a `healthy` class.
- The order of classes in `configs/classes.yaml` defines the numeric IDs. Never reorder them after training starts.
- All code reads the class list from `configs/classes.yaml`. **Do not hard-code class names.**

Known data issues to handle:

- **Crop imbalance:** tomato has 18,160 of 25,183 PlantVillage images (72%), corn 3,852 (15%), apple 3,171 (13%). Within classes the ratio between the largest (5,357) and smallest (275) is about 19 to 1. Report macro F1 and per-crop results, and use class weights or sampling.
- **Field coverage:** 15 of 18 classes have PlantDoc images. `apple__black_rot`, `corn__healthy` and `tomato__target_spot` have none, and `tomato__spider_mites` has only 2, so field evaluation covers 14 classes with a usable number of images. Report this coverage explicitly.
- **Small field set:** PlantDoc has only 1,395 images for these crops (54 to 192 per class), so split it carefully (see section 6) and expect noisy results.
- **Assumed PlantDoc labels:** "Apple leaf", "Tomato leaf" and "Corn leaf blight" are mapped by assumption. Check sample images before trusting them.
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