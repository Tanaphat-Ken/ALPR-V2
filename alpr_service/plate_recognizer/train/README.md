# TrOCR Fine-tuning PoC Toolkit

This directory packages everything needed to run the PoC described in your
plan: dataset preparation, configurable fine-tuning for two Thai TrOCR
checkpoints, evaluation utilities, and recommended experiment recipes.

## 1. Environment setup

Use the project virtual environment then install the extra libraries needed for
Hugging Face training:

```powershell
cd /d D:\CodingD\ALPR-V2\alpr_service\plate_recognizer
.\.venv\Scripts\activate
pip install "transformers[torch]" datasets accelerate peft sentencepiece "python-Levenshtein>=0.22" numpy
```

(If you plan to log to Weights & Biases add `wandb`.)

## 2. Dataset preparation

The CSV `data/tb_match_data_20240705_10581-11080.csv` already contains plate
crops (`image_name_gray`), labels, province codes, and validation flags.

`train/data_utils.py` exposes helpers to load and split the dataset.

Example – build manifests for later reuse:

```powershell
.\.venv\Scripts\python.exe - <<'PY'
from train import data_utils
records = data_utils.load_records(
    "data/tb_match_data_20240705_10581-11080.csv",
    data_roots=["data/210-20250930T155802Z-1-001"],
)
splits = data_utils.stratified_split(records, seed=42)
data_utils.export_manifest(splits, "train/manifests", include_metadata=True)
PY
```

This creates `train/manifests/train.jsonl`, `val.jsonl`, and `test.jsonl` which
feed directly into the evaluation script.

## 3. Training (`train_trocr.py`)

The training script supports both baseline checkpoints:

- `openthaigpt/thai-trocr`
- `kkatiz/thai-trocr-thaigov-v2`

and warm-starting from your internal V1 `.pth` weights. Key features:

- Stratified train/val/test splits and optional manifest export
- Pillow-based augmentations with presets (`--augment none|light|medium|heavy`)
- Mixed precision (`--fp16` or `--bf16`)
- LoRA fine-tuning (`--use-lora`, configurable rank/alpha/targets)
- Encoder freezing (`--freeze-encoder` / `--decoder-only`)
- Automatic validation & test evaluation with metric logging

### Minimal runs

Baseline (clean data, no LoRA):

```powershell
.\.venv\Scripts\python.exe train\train_trocr.py \
  --csv data\tb_match_data_20240705_10581-11080.csv \
  --data-root data\210-20250930T155802Z-1-001 \
  --model-id kkatiz/thai-trocr-thaigov-v2 \
  --augment none \
  --output-dir outputs\kkatiz_clean
```

Augmented + LoRA (recommended):

```powershell
.\.venv\Scripts\python.exe train\train_trocr.py \
  --csv data\tb_match_data_20240705_10581-11080.csv \
  --data-root data\210-20250930T155802Z-1-001 \
  --model-id kkatiz/thai-trocr-thaigov-v2 \
  --augment heavy \
  --use-lora --lora-rank 8 --lora-alpha 16 --lora-dropout 0.05 \
  --fp16 \
  --output-dir outputs\kkatiz_aug_lora \
  --report-to wandb  # optional
```

Continuation from V1 weights:

```powershell
.\.venv\Scripts\python.exe train\train_trocr.py \
  --csv data\tb_match_data_20240705_10581-11080.csv \
  --data-root data\210-20250930T155802Z-1-001 \
  --model-id openthaigpt/thai-trocr \
  --model-path models\weights\charactor_reader.pth \
  --augment medium \
  --freeze-encoder \
  --output-dir outputs\v1_medium
```

`train_trocr.py --help` lists every option (batch sizes, schedulers, manifests,
resume, etc.).

## 4. Evaluation (`eval_trocr.py`)

Use this script to benchmark CER, exact-match accuracy, and latency. You can
point it either at the CSV (it will regenerate splits with the same seed) or at
the manifests saved earlier.

Example using the generated manifests:

```powershell
.\.venv\Scripts\python.exe train\eval_trocr.py \
  --manifest train\manifests\test.jsonl \
  --model-path outputs\kkatiz_aug_lora \
  --model-id kkatiz/thai-trocr-thaigov-v2 \
  --num-beams 5 --batch-size 8 --normalize-text \
  --save-results outputs\kkatiz_aug_lora\test_results.json
```

Example directly from CSV (recomputes split with `seed=42`):

```powershell
.\.venv\Scripts\python.exe train\eval_trocr.py \
  --csv data\tb_match_data_20240705_10581-11080.csv \
  --data-root data\210-20250930T155802Z-1-001 \
  --model-path outputs\v1_medium \
  --model-id openthaigpt/thai-trocr \
  --split test --num-beams 5 --batch-size 4
```

The script prints metrics to STDOUT and (optionally) writes a detailed JSON file
with per-sample predictions.

## 5. Recommended experiment grid

| #   | Model init  | Data      | Augment | Special        | Notes                                 |
| --- | ----------- | --------- | ------- | -------------- | ------------------------------------- |
| 1   | V1 (.pth)   | Clean     | none    | freeze encoder | Baseline continuation                 |
| 2   | V1 (.pth)   | Augmented | heavy   | LoRA (rank=8)  | Measures impact of augment + adapters |
| 3   | kkatiz      | Clean     | none    | full fine-tune | Direct baseline                       |
| 4   | kkatiz      | Augmented | heavy   | LoRA           | Primary candidate                     |
| 5   | openthaigpt | Augmented | medium  | LoRA           | Backup checkpoint                     |

Track `cer`, `exact_match`, `latency_ms`, `throughput_ips` from `eval_trocr.py`
and compare against the preprocessing-only baseline previously measured.

## 6. Tips & troubleshooting

- GPU memory tight? Add `--gradient-accumulation-steps 2` and reduce per-device
  batch size to 4.
- If augmentations make training unstable, switch to `--augment light`.
- To resume a run: `--resume-from-checkpoint outputs\kkatiz_aug_lora\checkpoint-XXXX`.
- For LoRA export, keep the `adapter_config.json` + `adapter_model.bin` from the
  output directory; use `peft`'s `PeftModel.from_pretrained` during inference.
- Keep raw checkpoints out of Git: store under `outputs/` (already ignored) and
  push selected weights to an artifact store or release tag instead.

With these utilities you can reproduce the three requested PoC tracks (baseline,
clean fine-tune, augmented fine-tune) across both reference models and produce a
concise report for stakeholders.

## 7. Automating the full grid

Use `train/run_experiments.py` to execute the five scenarios above in one go.
It will launch `train_trocr.py` followed by `eval_trocr.py` for each experiment,
dropping artefacts under a dedicated subfolder in `outputs/grid/`.

Dry-run the pipeline first to inspect the generated commands:

```powershell
.\.venv\Scripts\python.exe train\run_experiments.py `
  --csv data\tb_match_data_20240705_10581-11080.csv `
  --data-root data\210-20250930T155802Z-1-001 `
  --dry-run
```

Run the full grid (training + evaluation):

```powershell
.\.venv\Scripts\python.exe train\run_experiments.py `
  --csv data\tb_match_data_20240705_10581-11080.csv `
  --data-root data\210-20250930T155802Z-1-001 `
  --output-root outputs\grid
```

Helpful switches:

- `--stage train` / `--stage eval` to run only one stage
- `--experiments exp2_v1_aug_lora exp4_kkatiz_aug_lora` to target specific rows
- `--skip-existing` to avoid retraining when weights are already present
- `--max-train-samples 128 --eval-max-samples 64` for smoke tests
- `--continue-on-error` to carry on even if one run fails

Each evaluation writes a JSON report to `<output>/eval_test.json` with CER,
exact-match accuracy, latency, throughput, and per-sample predictions
(when executed without `--dry-run`).
