"""Automation helper to execute the recommended TrOCR fine-tuning grid.

This script sequentially launches ``train_trocr.py`` and ``eval_trocr.py`` for
each experiment scenario defined in the README table. It accepts dataset paths,
lets you select specific experiments, and optionally skips stages when results
already exist.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
TRAIN_SCRIPT = SCRIPT_DIR / "train_trocr.py"
EVAL_SCRIPT = SCRIPT_DIR / "eval_trocr.py"


@dataclass(frozen=True)
class Experiment:
    key: str
    description: str
    train_args: Sequence[str]
    eval_args: Sequence[str]
    use_lora: bool = False
    output_name: str | None = None

    def output_dir(self, base_dir: Path) -> Path:
        return base_dir / (self.output_name or self.key)


EXPERIMENTS: List[Experiment] = [
    Experiment(
        key="exp1_v1_clean",
        description="V1 (.pth) baseline continuation with clean data (freeze encoder)",
        train_args=[
            "--model-id",
            "openthaigpt/thai-trocr",
            "--model-path",
            "models/weights/charactor_reader.pth",
            "--augment",
            "none",
            "--freeze-encoder",
        ],
        eval_args=[
            "--model-id",
            "openthaigpt/thai-trocr",
            "--split",
            "test",
        ],
        use_lora=False,
        output_name="exp1_v1_clean",
    ),
    Experiment(
        key="exp2_v1_aug_lora",
        description="V1 (.pth) with heavy augmentation + LoRA adapters",
        train_args=[
            "--model-id",
            "openthaigpt/thai-trocr",
            "--model-path",
            "models/weights/charactor_reader.pth",
            "--augment",
            "heavy",
            "--use-lora",
            "--lora-target-modules",
            "auto",
            "--lora-scope",
            "decoder",
            "--lora-rank",
            "8",
            "--lora-alpha",
            "16",
            "--lora-dropout",
            "0.05",
            "--fp16",
        ],
        eval_args=[
            "--model-id",
            "openthaigpt/thai-trocr",
            "--split",
            "test",
        ],
        use_lora=True,
        output_name="exp2_v1_aug_lora",
    ),
    Experiment(
        key="exp3_kkatiz_clean",
        description="kkatiz baseline fine-tune on clean data",
        train_args=[
            "--model-id",
            "kkatiz/thai-trocr-thaigov-v2",
            "--augment",
            "none",
            "--fp16",
        ],
        eval_args=[
            "--model-id",
            "kkatiz/thai-trocr-thaigov-v2",
            "--split",
            "test",
        ],
        use_lora=False,
        output_name="exp3_kkatiz_clean",
    ),
    Experiment(
        key="exp4_kkatiz_aug_lora",
        description="kkatiz with heavy augmentation + LoRA adapters",
        train_args=[
            "--model-id",
            "kkatiz/thai-trocr-thaigov-v2",
            "--augment",
            "heavy",
            "--use-lora",
            "--lora-target-modules",
            "auto",
            "--lora-scope",
            "decoder",
            "--lora-rank",
            "8",
            "--lora-alpha",
            "16",
            "--lora-dropout",
            "0.05",
            "--fp16",
        ],
        eval_args=[
            "--model-id",
            "kkatiz/thai-trocr-thaigov-v2",
            "--split",
            "test",
        ],
        use_lora=True,
        output_name="exp4_kkatiz_aug_lora",
    ),
    Experiment(
        key="exp5_openthaigpt_aug_lora",
        description="openthaigpt checkpoint with medium augmentation + LoRA",
        train_args=[
            "--model-id",
            "openthaigpt/thai-trocr",
            "--augment",
            "medium",
            "--use-lora",
            "--lora-target-modules",
            "auto",
            "--lora-scope",
            "decoder",
            "--lora-rank",
            "8",
            "--lora-alpha",
            "16",
            "--lora-dropout",
            "0.05",
            "--fp16",
        ],
        eval_args=[
            "--model-id",
            "openthaigpt/thai-trocr",
            "--split",
            "test",
        ],
        use_lora=True,
        output_name="exp5_openthaigpt_aug_lora",
    ),
]

EXPERIMENT_LOOKUP = {exp.key: exp for exp in EXPERIMENTS}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the recommended TrOCR experiment grid")
    parser.add_argument("--csv", required=True, help="Path to tb_match_data_*.csv")
    parser.add_argument("--data-root", action="append", required=True, help="Root directory containing the /210/... hierarchy.")
    parser.add_argument(
        "--experiments",
        nargs="*",
        default=[exp.key for exp in EXPERIMENTS],
        help="Keys of experiments to run (default: all).",
    )
    parser.add_argument(
        "--stage",
        choices=["train", "eval", "both"],
        default="both",
        help="Which stage(s) to execute for each experiment.",
    )
    parser.add_argument("--output-root", default="outputs/grid", help="Directory to store experiment outputs.")
    parser.add_argument("--max-train-samples", type=int, help="Optional cap on training samples (for quick smoke tests).")
    parser.add_argument("--max-eval-samples", type=int, help="Optional cap on eval samples during training.")
    parser.add_argument("--eval-max-samples", type=int, help="Optional cap on samples during standalone evaluation.")
    parser.add_argument("--eval-num-beams", type=int, default=5)
    parser.add_argument("--eval-batch-size", type=int, default=8)
    parser.add_argument(
        "--num-workers",
        type=int,
        default=0,
        help="PyTorch DataLoader workers for train/eval (0 is Windows-safe; raise on Linux).",
    )
    parser.add_argument("--eval-normalize-text", action="store_true")
    parser.add_argument("--skip-existing", action="store_true", help="Skip training if output dir already has weights.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without executing them.")
    parser.add_argument("--continue-on-error", action="store_true", help="Keep going even if a command fails.")
    return parser.parse_args()


def build_command(base: Sequence[str], extra: Sequence[str]) -> List[str]:
    return list(base) + list(extra)


def run_command(cmd: Sequence[str], *, dry_run: bool) -> int:
    cmd_display = " ".join(str(x) for x in cmd)
    print(f"\n==> Running: {cmd_display}")
    if dry_run:
        print("[dry-run] command not executed")
        return 0
    completed = subprocess.run(cmd, cwd=PROJECT_ROOT)
    if completed.returncode != 0:
        print(f"[error] Command failed with exit code {completed.returncode}")
    return completed.returncode


def has_existing_weights(output_dir: Path) -> bool:
    return (
        (output_dir / "pytorch_model.bin").exists()
        or (output_dir / "model.safetensors").exists()
        or (output_dir / "adapter_model.bin").exists()
        or (output_dir / "adapter_model.safetensors").exists()
        or (output_dir / "adapter_model.pt").exists()
    )


def main() -> None:
    args = parse_args()

    selected_experiments = []
    for key in args.experiments:
        if key not in EXPERIMENT_LOOKUP:
            raise SystemExit(f"Unknown experiment key: {key}")
        selected_experiments.append(EXPERIMENT_LOOKUP[key])

    output_root = Path(args.output_root).resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    train_common: List[str] = ["--csv", args.csv]
    for root in args.data_root:
        train_common.extend(["--data-root", root])

    train_common.extend(["--num-workers", str(args.num_workers)])

    if args.max_train_samples is not None:
        train_common.extend(["--max-train-samples", str(args.max_train_samples)])
    if args.max_eval_samples is not None:
        train_common.extend(["--max-eval-samples", str(args.max_eval_samples)])

    eval_common: List[str] = [
        "--csv",
        args.csv,
    ]
    for root in args.data_root:
        eval_common.extend(["--data-root", root])
    eval_common.extend([
        "--num-beams",
        str(args.eval_num_beams),
        "--batch-size",
        str(args.eval_batch_size),
    ])
    if args.eval_max_samples is not None:
        eval_common.extend(["--max-samples", str(args.eval_max_samples)])
    if args.eval_normalize_text:
        eval_common.append("--normalize-text")

    for exp in selected_experiments:
        print(f"\n=== Experiment: {exp.key} ===\n{exp.description}")
        out_dir = exp.output_dir(output_root)
        out_dir.mkdir(parents=True, exist_ok=True)

        if args.stage in ("train", "both"):
            if args.skip_existing and has_existing_weights(out_dir):
                print(f"[skip] Weights already present in {out_dir}, skipping training stage.")
            else:
                train_cmd = build_command(
                    [str(sys.executable), str(TRAIN_SCRIPT)],
                    train_common
                    + ["--output-dir", str(out_dir)]
                    + list(exp.train_args),
                )
                code = run_command(train_cmd, dry_run=args.dry_run)
                if code != 0 and not args.continue_on_error:
                    raise SystemExit(code)

        if args.stage in ("eval", "both"):
            eval_cmd = build_command(
                [str(sys.executable), str(EVAL_SCRIPT)],
                eval_common
                + ["--model-path", str(out_dir)]
                + list(exp.eval_args)
                + (["--use-lora"] if exp.use_lora else []),
            )
            save_results = out_dir / "eval_test.json"
            eval_cmd.extend(["--save-results", str(save_results)])
            code = run_command(eval_cmd, dry_run=args.dry_run)
            if code != 0 and not args.continue_on_error:
                raise SystemExit(code)

    print("\nAll requested experiments processed.")


if __name__ == "__main__":  # pragma: no cover
    main()
