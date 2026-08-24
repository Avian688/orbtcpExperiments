#!/usr/bin/env python3
"""Run aggregate plots for the final OrbCC and a full-INT diagnostic view."""

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
PLOT_SUFFIXES = {".csv", ".json", ".pdf", ".png", ".svg"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate final OrbCC and optional full-INT diagnostic plot variants."
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


def comparison_path(path: Path) -> Path:
    if path.name.endswith(".csv.metadata.json"):
        stem = path.name[: -len(".csv.metadata.json")]
        return path.with_name(stem + "_with_orbtcp.csv.metadata.json")
    return path.with_name(path.stem + "_with_orbtcp" + path.suffix)


def run_plot(script: Path, script_args: list[str], cwd: Path, variant: str) -> None:
    env = os.environ.copy()
    env[PLOT_VARIANT_ENV] = variant
    result = subprocess.run([sys.executable, str(script), *script_args], cwd=cwd, env=env)
    if result.returncode != 0:
        raise RuntimeError(f"{script.name} ({variant}) failed with exit code {result.returncode}")


def main() -> int:
    args = parse_args()
    cwd = Path.cwd().resolve()
    script = args.script.resolve()
    if not script.is_file():
        raise FileNotFoundError(f"Plot script not found: {script}")

    before_main = snapshot_files(cwd)
    run_plot(script, args.script_args, cwd, MAIN_VARIANT)
    main_outputs = changed_files(before_main, snapshot_files(cwd))
    if not main_outputs:
        print(f"{script.name}: no plot outputs changed; skipping full-INT comparison copy")
        return 0

    with tempfile.TemporaryDirectory(prefix="orbtcp-plot-main-") as temporary_dir:
        backup_root = Path(temporary_dir)
        for relative_path in main_outputs:
            source = cwd / relative_path
            backup = backup_root / relative_path
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, backup)

        before_comparison = snapshot_files(cwd)
        run_plot(script, args.script_args, cwd, COMPARISON_VARIANT)
        comparison_outputs = changed_files(before_comparison, snapshot_files(cwd))

        for relative_path in sorted(comparison_outputs):
            source = cwd / relative_path
            comparison = comparison_path(source)
            shutil.copy2(source, comparison)
            if relative_path in main_outputs:
                shutil.copy2(backup_root / relative_path, source)
            else:
                source.unlink()
            print(f"Saved full-INT comparison: {comparison.relative_to(cwd)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
