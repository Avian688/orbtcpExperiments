#!/usr/bin/env python3
"""Generate main plot variants with optional BBRv1 and full-INT views."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


PLOT_VARIANT_ENV = "ORBTCP_PLOT_VARIANT"
MAIN_VARIANT = "pint"
COMPARISON_VARIANT = "with_orbtcp"
PLOT_BBRV1_ENV = "ORBTCP_PLOT_BBRV1"
WITH_BBRV1 = "with_bbrv1"
WITHOUT_BBRV1 = "without_bbrv1"
PLOT_SUFFIXES = {".csv", ".json", ".pdf", ".png", ".svg"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate final OrbCC plots with and without BBRv1, plus the "
            "full-INT diagnostic variant."
        )
    )
    parser.add_argument("script", type=Path, help="Aggregate plot script to run")
    parser.add_argument("script_args", nargs=argparse.REMAINDER, help="Arguments passed to the plot script")
    return parser.parse_args()


def snapshot_files(root: Path) -> dict[Path, tuple[int, int]]:
    return {
        path.relative_to(root): (path.stat().st_mtime_ns, path.stat().st_size)
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in PLOT_SUFFIXES
    }


def changed_files(before: dict[Path, tuple[int, int]], after: dict[Path, tuple[int, int]]) -> set[Path]:
    return {path for path, stat in after.items() if before.get(path) != stat}


def suffixed_path(path: Path, suffix: str) -> Path:
    if path.name.endswith(".csv.metadata.json"):
        stem = path.name[: -len(".csv.metadata.json")]
        return path.with_name(stem + suffix + ".csv.metadata.json")
    return path.with_name(path.stem + suffix + path.suffix)


def run_plot(
    script: Path,
    script_args: list[str],
    cwd: Path,
    orbcc_variant: str,
    bbrv1_variant: str,
) -> None:
    env = os.environ.copy()
    env[PLOT_VARIANT_ENV] = orbcc_variant
    env[PLOT_BBRV1_ENV] = bbrv1_variant
    result = subprocess.run([sys.executable, str(script), *script_args], cwd=cwd, env=env)
    if result.returncode != 0:
        raise RuntimeError(
            f"{script.name} ({orbcc_variant}, {bbrv1_variant}) failed "
            f"with exit code {result.returncode}"
        )


def save_derived_variant(
    script: Path,
    script_args: list[str],
    cwd: Path,
    orbcc_variant: str,
    bbrv1_variant: str,
    suffix: str,
    description: str,
    main_outputs: set[Path],
    backup_root: Path,
) -> None:
    before = snapshot_files(cwd)
    run_plot(script, script_args, cwd, orbcc_variant, bbrv1_variant)
    outputs = changed_files(before, snapshot_files(cwd))

    for relative_path in sorted(outputs):
        source = cwd / relative_path
        derived = suffixed_path(source, suffix)
        shutil.copy2(source, derived)
        if relative_path in main_outputs:
            shutil.copy2(backup_root / relative_path, source)
        else:
            source.unlink()
        print(f"Saved {description}: {derived.relative_to(cwd)}")


def main() -> int:
    args = parse_args()
    cwd = Path.cwd().resolve()
    script = args.script.resolve()
    if not script.is_file():
        raise FileNotFoundError(f"Plot script not found: {script}")

    before_main = snapshot_files(cwd)
    run_plot(script, args.script_args, cwd, MAIN_VARIANT, WITH_BBRV1)
    main_outputs = changed_files(before_main, snapshot_files(cwd))
    if not main_outputs:
        print(f"{script.name}: no plot outputs changed; skipping derived variants")
        return 0

    with tempfile.TemporaryDirectory(prefix="orbtcp-plot-main-") as temporary_dir:
        backup_root = Path(temporary_dir)
        for relative_path in main_outputs:
            source = cwd / relative_path
            backup = backup_root / relative_path
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, backup)

        save_derived_variant(
            script,
            args.script_args,
            cwd,
            MAIN_VARIANT,
            WITHOUT_BBRV1,
            "_without_bbrv1",
            "main plot without BBRv1",
            main_outputs,
            backup_root,
        )
        save_derived_variant(
            script,
            args.script_args,
            cwd,
            COMPARISON_VARIANT,
            WITH_BBRV1,
            "_with_orbtcp",
            "full-INT comparison",
            main_outputs,
            backup_root,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
