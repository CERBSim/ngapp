"""Compare test output images against baselines side-by-side.

Usage::

    python -m ngapp.compare_test_images path/to/tests
    python -m ngapp.compare_test_images path/to/tests --only-errors
    python -m ngapp.compare_test_images path/to/tests --only-baseline
    python -m ngapp.compare_test_images --git-diff
"""

import argparse
import io
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image
import matplotlib.pyplot as plt

PAGE_SIZE = 10


def _has_diff(out_img: np.ndarray, ref_img: np.ndarray) -> bool:
    if out_img.shape != ref_img.shape:
        return True
    diff = np.abs(out_img.astype(int) - ref_img.astype(int))
    return (diff.max(axis=-1) > 2).sum() > 0


def _show_baseline_grid(names: list[str], baseline_dir: Path) -> None:
    """Show baseline images in pages of PAGE_SIZE, arranged in a grid."""
    for page_start in range(0, len(names), PAGE_SIZE):
        batch = names[page_start : page_start + PAGE_SIZE]
        n = len(batch)
        cols = min(n, 5)
        rows = math.ceil(n / cols)

        fig, axes = plt.subplots(rows, cols, figsize=(4 * cols, 4 * rows))
        axes = np.atleast_1d(axes).flatten()

        for i, name in enumerate(batch):
            img = np.array(Image.open(baseline_dir / name))
            axes[i].imshow(img)
            axes[i].set_title(name, fontsize=9)
            axes[i].axis("off")

        for i in range(n, len(axes)):
            axes[i].axis("off")

        page_num = page_start // PAGE_SIZE + 1
        total_pages = math.ceil(len(names) / PAGE_SIZE)
        fig.suptitle(f"Baselines  (page {page_num}/{total_pages})", fontsize=14)
        fig.tight_layout()
        print(f"Page {page_num}/{total_pages} — close window for next")
        plt.show(block=True)


def _git_toplevel() -> Path:
    """Return the absolute path to the git repo root."""
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, check=True,
    )
    return Path(result.stdout.strip())


def _get_git_diff_pngs(filter_dir: Path | None = None) -> list[Path]:
    """Return repo-relative paths of .png files in git diff.

    If *filter_dir* is given, only return PNGs whose absolute path is
    inside that directory.
    """
    toplevel = _git_toplevel()
    result = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=ACMR", "HEAD"],
        capture_output=True, text=True, check=True,
    )
    repo_paths = sorted(
        Path(line) for line in result.stdout.splitlines()
        if line.lower().endswith(".png")
    )
    if filter_dir is not None:
        resolved = filter_dir.resolve()
        repo_paths = [
            p for p in repo_paths
            if (toplevel / p).resolve().is_relative_to(resolved)
        ]
    return repo_paths


def _git_show_image(repo_path: Path) -> np.ndarray | None:
    """Load the HEAD version of a repo-relative file, or None if new."""
    try:
        git_show = subprocess.Popen(
            ["git", "show", f"HEAD:{repo_path}"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        )
        smudge = subprocess.Popen(
            ["git", "lfs", "smudge"],
            stdin=git_show.stdout, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        )
        git_show.stdout.close()
        data, _ = smudge.communicate()
        if git_show.wait() != 0 or smudge.returncode != 0:
            return None
    except (subprocess.SubprocessError, OSError):
        return None
    return np.array(Image.open(io.BytesIO(data)))


def _compare_git_diff(filter_dir: Path | None = None) -> None:
    """Compare all PNGs in git diff against their HEAD versions."""
    toplevel = _git_toplevel()
    repo_paths = _get_git_diff_pngs(filter_dir)
    if not repo_paths:
        sys.exit("No changed .png files in git diff.")

    print(f"Found {len(repo_paths)} changed PNG(s) in git diff.")
    for repo_path in repo_paths:
        abs_path = toplevel / repo_path
        new_img = np.array(Image.open(abs_path))
        old_img = _git_show_image(repo_path)

        if old_img is None:
            fig, ax = plt.subplots(1, 1, figsize=(6, 5))
            fig.suptitle(f"{repo_path}  [NEW]", fontsize=14)
            ax.imshow(new_img)
            ax.set_title("New")
            ax.axis("off")
            fig.tight_layout()
            print(f"{repo_path} [NEW] — close window for next")
            plt.show(block=True)
            continue

        has_error = _has_diff(new_img, old_img)
        if not has_error:
            continue

        if new_img.shape == old_img.shape:
            diff = np.clip(
                np.abs(new_img.astype(int) - old_img.astype(int)) * 10, 0, 255
            ).astype(np.uint8)
        else:
            diff = np.zeros_like(new_img)

        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        fig.suptitle(f"{repo_path}  [DIFF]", fontsize=14)

        axes[0].imshow(old_img)
        axes[0].set_title("HEAD (old)")
        axes[0].axis("off")

        axes[1].imshow(new_img)
        axes[1].set_title("Working tree (new)")
        axes[1].axis("off")

        axes[2].imshow(diff)
        axes[2].set_title("Diff (×10)")
        axes[2].axis("off")

        fig.tight_layout()
        print(f"{repo_path} [DIFF] — close window for next")
        plt.show(block=True)

    print("Done.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare test output vs baselines."
    )
    parser.add_argument(
        "test_dir",
        nargs="?",
        type=Path,
        help="Test directory containing 'output' and 'baselines' subdirs.",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--only-errors",
        action="store_true",
        help="Only show images that differ.",
    )
    group.add_argument(
        "--only-baseline",
        action="store_true",
        help="Only show baseline images in a grid.",
    )
    group.add_argument(
        "--git-diff",
        action="store_true",
        help="Compare all PNGs in git diff against their HEAD versions.",
    )
    args = parser.parse_args()

    if args.git_diff:
        _compare_git_diff(args.test_dir)
        return

    if args.test_dir is None:
        parser.error("test_dir is required unless --git-diff is used")

    baseline_dir = args.test_dir / "baselines"
    output_dir = args.test_dir / "output"

    if not baseline_dir.is_dir():
        sys.exit(f"Baseline directory not found: {baseline_dir}")

    if args.only_baseline:
        names = sorted(p.name for p in baseline_dir.glob("*.png"))
        if not names:
            sys.exit("No baseline images found.")
        _show_baseline_grid(names, baseline_dir)
        print("Done.")
        return

    if not output_dir.is_dir():
        sys.exit(f"Output directory not found: {output_dir}")

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
            diff = np.clip(
                np.abs(out_img.astype(int) - ref_img.astype(int)) * 10, 0, 255
            ).astype(np.uint8)
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
        print(f"{name}{status} — close window for next")
        plt.show(block=True)

    print("Done.")


if __name__ == "__main__":
    main()
