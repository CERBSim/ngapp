"""Compare test output images against baselines side-by-side.

Usage::

    python -m ngapp.compare_test_images path/to/tests
    python -m ngapp.compare_test_images path/to/tests --only-errors
"""

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image
import matplotlib.pyplot as plt


def _has_diff(out_img: np.ndarray, ref_img: np.ndarray) -> bool:
    if out_img.shape != ref_img.shape:
        return True
    diff = np.abs(out_img.astype(int) - ref_img.astype(int))
    return (diff.max(axis=-1) > 2).sum() > 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare test output vs baselines.")
    parser.add_argument(
        "test_dir",
        type=Path,
        help="Test directory containing 'output' and 'baselines' subdirs.",
    )
    parser.add_argument(
        "--only-errors",
        action="store_true",
        help="Only show images that differ.",
    )
    args = parser.parse_args()

    output_dir = args.test_dir / "output"
    baseline_dir = args.test_dir / "baselines"

    if not output_dir.is_dir():
        sys.exit(f"Output directory not found: {output_dir}")
    if not baseline_dir.is_dir():
        sys.exit(f"Baseline directory not found: {baseline_dir}")

    # Collect matching image pairs (skip diff_ files)
    names = sorted(
        p.name
        for p in output_dir.glob("*.png")
        if not p.name.startswith("diff_") and (baseline_dir / p.name).exists()
    )

    if not names:
        sys.exit("No matching image pairs found.")

    for name in names:
        out_img = np.array(Image.open(output_dir / name))
        ref_img = np.array(Image.open(baseline_dir / name))

        has_error = _has_diff(out_img, ref_img)

        if args.only_errors and not has_error:
            continue

        if out_img.shape == ref_img.shape:
            diff = np.clip(np.abs(out_img.astype(int) - ref_img.astype(int)) * 10, 0, 255).astype(np.uint8)
        else:
            diff = np.zeros_like(out_img)

        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        status = " [DIFF]" if has_error else " [OK]"
        fig.suptitle(f"{name}{status}", fontsize=14)

        axes[0].imshow(ref_img)
        axes[0].set_title("Baseline")
        axes[0].axis("off")

        axes[1].imshow(out_img)
        axes[1].set_title("Output")
        axes[1].axis("off")

        axes[2].imshow(diff)
        axes[2].set_title("Diff (×10)")
        axes[2].axis("off")

        fig.tight_layout()
        print(f"{name}{status} — press Enter for next, q to quit")
        plt.show(block=True)

    print("Done.")


if __name__ == "__main__":
    main()