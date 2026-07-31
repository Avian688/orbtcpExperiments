#!/usr/bin/env python3

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent))

from experiment13Support import (
    FULL_ORBCC,
    PINT_VARIANTS,
    RUNS,
    VARIANTS,
    WORKLOADS,
    config_name,
    ini_name,
)
from raynetExperimentSupport import collect_simulation_configs, run_simulation_configs


EXPERIMENT_DIR = (SCRIPT_DIR / "../../paperExperiments/experiment13").resolve()


def run_checked(command: list[str], cwd: Path) -> None:
    print(" ".join(str(part) for part in command))
    subprocess.run(command, cwd=cwd, check=True)


def wait_for_batch(active: list[tuple[str, subprocess.Popen]]) -> None:
    failures = []
    for label, process in active:
        status = process.wait()
        if status == 0:
            print(f"Completed {label}")
        else:
            failures.append(f"{label}={status}")
    if failures:
        raise RuntimeError("Experiment 13 batch failed: " + ", ".join(failures))


def batched(commands: list[tuple[str, list[str]]], cwd: Path, cores: int) -> None:
    active: list[tuple[str, subprocess.Popen]] = []
    for label, command in commands:
        print(f"Starting {label}")
        active.append((label, subprocess.Popen(command, cwd=cwd)))
        if len(active) >= cores:
            wait_for_batch(active)
            active.clear()
    wait_for_batch(active)


def cases():
    for variant in VARIANTS:
        for workload in WORKLOADS:
            for run in RUNS:
                yield variant, workload, run, config_name(variant, workload, run)


def generate_inputs() -> None:
    run_checked([sys.executable, "generateExperiment13Scenarios.py"], SCRIPT_DIR)
    run_checked([sys.executable, "generateExperiment13IniFile.py"], SCRIPT_DIR)


def simulation_configs():
    groups = (
        (FULL_ORBCC.protocol, ini_name(FULL_ORBCC), (FULL_ORBCC,)),
        (PINT_VARIANTS[0].protocol, ini_name(PINT_VARIANTS[0]), PINT_VARIANTS),
    )
    all_configs = []
    for protocol, ini_file, variants in groups:
        configs = collect_simulation_configs(protocol, ini_file, RUNS, EXPERIMENT_DIR)
        expected = {
            config_name(variant, workload, run)
            for variant in variants
            for workload in WORKLOADS
            for run in RUNS
        }
        found = {config.config_name for config in configs}
        if found != expected:
            missing = sorted(expected - found)
            unexpected = sorted(found - expected)
            raise RuntimeError(
                f"Unexpected Experiment 13 configs in {ini_file}: "
                f"missing={missing}, unexpected={unexpected}"
            )
        all_configs.extend(configs)
    return all_configs


def run_simulations(cores: int) -> None:
    (EXPERIMENT_DIR / "results").mkdir(parents=True, exist_ok=True)
    runtime_file = SCRIPT_DIR / "experiment13runTimes.txt"
    runtime_file.unlink(missing_ok=True)
    with runtime_file.open("w", encoding="utf-8") as output:
        output.write("-- Experiment 13 Runtimes (s) --")
        run_simulation_configs(simulation_configs(), EXPERIMENT_DIR, cores, output)


def expected_vec_files():
    for _variant, _workload, _run, name in cases():
        yield EXPERIMENT_DIR / "results" / f"{name}-#0.vec"


def export_csvs(cores: int) -> None:
    commands = []
    for vec_file in expected_vec_files():
        if not vec_file.is_file() or vec_file.stat().st_size == 0:
            raise FileNotFoundError(f"Missing simulation output: {vec_file}")
        csv_name = vec_file.name.removesuffix("-#0.vec") + ".csv"
        commands.append(
            (
                csv_name,
                [
                    "opp_scavetool",
                    "export",
                    "-o",
                    str(Path("results") / csv_name),
                    "-F",
                    "CSV-R",
                    str(Path("results") / vec_file.name),
                ],
            )
        )
    batched(commands, EXPERIMENT_DIR, cores)


def extract_csvs(cores: int) -> None:
    commands = []
    for variant, workload, run, name in cases():
        csv_file = EXPERIMENT_DIR / "results" / f"{name}.csv"
        if not csv_file.is_file() or csv_file.stat().st_size == 0:
            raise FileNotFoundError(f"Missing exported CSV: {csv_file}")
        commands.append(
            (
                f"extract {variant.key} {workload} run{run}",
                [
                    sys.executable,
                    "extractSingleCsvFile.py",
                    str(csv_file),
                    variant.key,
                    workload,
                    str(run),
                ],
            )
        )
    batched(commands, SCRIPT_DIR, cores)


def plot() -> None:
    run_checked([sys.executable, "plotPintProbability.py"], SCRIPT_DIR)


def main() -> int:
    cores = max(1, int(os.environ.get("EXPERIMENT_CORES", "1")))
    start_step = int(os.environ.get("START_STEP", "1"))
    end_step = int(os.environ.get("END_STEP", "5"))
    steps = [
        ("generate scenarios and ini files", generate_inputs),
        ("run simulations", lambda: run_simulations(cores)),
        ("export scavetool CSVs", lambda: export_csvs(cores)),
        ("extract plotting CSVs", lambda: extract_csvs(cores)),
        ("plot per-run and aggregate probability results", plot),
    ]

    for index, (name, function) in enumerate(steps, start=1):
        if start_step <= index <= end_step:
            print(f"Experiment 13 step {index}: {name}")
            function()
        else:
            print(f"Skipping Experiment 13 step {index}: {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
