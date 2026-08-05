#!/usr/bin/env python3

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent))

from experimentTuningDynamicSupport import (  # noqa: E402
    CONDITIONS,
    EXPERIMENT,
    FLOW_COUNTS,
    FULL_ORBCC,
    PINT_VARIANTS,
    RUNS,
    VARIANTS,
    cases,
    config_name,
    expected_simulation_count,
    ini_name,
)
from raynetExperimentSupport import (  # noqa: E402
    collect_simulation_configs,
    run_simulation_configs,
)


EXPERIMENT_DIR = (SCRIPT_DIR / "../../paperExperiments" / EXPERIMENT).resolve()


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
        raise RuntimeError(f"{EXPERIMENT} batch failed: " + ", ".join(failures))


def batched(commands: list[tuple[str, list[str]]], cwd: Path, cores: int) -> None:
    active: list[tuple[str, subprocess.Popen]] = []
    for label, command in commands:
        print(f"Starting {label}")
        active.append((label, subprocess.Popen(command, cwd=cwd)))
        if len(active) >= cores:
            wait_for_batch(active)
            active.clear()
    wait_for_batch(active)


def named_cases():
    for variant, flow_count, condition, run in cases():
        yield (
            variant,
            flow_count,
            condition,
            run,
            config_name(variant, flow_count, condition, run),
        )


def generate_inputs() -> None:
    run_checked(
        [sys.executable, "generateExperimentTuningDynamicScenarios.py"],
        SCRIPT_DIR,
    )
    run_checked(
        [sys.executable, "generateExperimentTuningDynamicIniFile.py"],
        SCRIPT_DIR,
    )


def simulation_configs():
    groups = (
        ("orbtcp", ini_name(False), (FULL_ORBCC,)),
        ("orbtcp_pint", ini_name(True), PINT_VARIANTS),
    )
    all_configs = []
    for protocol, ini_file, variants in groups:
        configs = collect_simulation_configs(
            protocol, ini_file, RUNS, EXPERIMENT_DIR
        )
        expected = {
            config_name(variant, flow_count, condition, run)
            for variant in variants
            for flow_count in FLOW_COUNTS
            for condition in CONDITIONS
            for run in RUNS
        }
        found = {config.config_name for config in configs}
        if found != expected:
            missing = sorted(expected - found)
            unexpected = sorted(found - expected)
            raise RuntimeError(
                f"Unexpected {EXPERIMENT} configs in {ini_file}: "
                f"missing={missing}, unexpected={unexpected}"
            )
        all_configs.extend(configs)
    if len(all_configs) != expected_simulation_count():
        raise RuntimeError(
            f"Expected {expected_simulation_count()} configs, found {len(all_configs)}"
        )
    return all_configs


def run_simulations(cores: int) -> None:
    (EXPERIMENT_DIR / "results").mkdir(parents=True, exist_ok=True)
    runtime_file = SCRIPT_DIR / "experimentTuningDynamicRunTimes.txt"
    runtime_file.unlink(missing_ok=True)
    with runtime_file.open("w", encoding="utf-8") as output:
        output.write("-- Experiment Tuning Dynamic Runtimes (s) --")
        run_simulation_configs(
            simulation_configs(), EXPERIMENT_DIR, cores, output
        )


def expected_vec_files():
    for _variant, _flow_count, _condition, _run, name in named_cases():
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
    for variant, flow_count, condition, run, name in named_cases():
        csv_file = EXPERIMENT_DIR / "results" / f"{name}.csv"
        if not csv_file.is_file() or csv_file.stat().st_size == 0:
            raise FileNotFoundError(f"Missing exported CSV: {csv_file}")
        commands.append(
            (
                f"extract {variant.key} {condition.key} {flow_count}flows run{run}",
                [
                    sys.executable,
                    "extractSingleCsvFile.py",
                    str(csv_file),
                    variant.key,
                    condition.key,
                    str(flow_count),
                    str(run),
                ],
            )
        )
    batched(commands, SCRIPT_DIR, cores)


def plot() -> None:
    run_checked([sys.executable, "plotExperimentTuningDynamic.py"], SCRIPT_DIR)


def main() -> int:
    cores = max(1, int(os.environ.get("EXPERIMENT_CORES", "1")))
    start_step = int(os.environ.get("START_STEP", "1"))
    end_step = int(os.environ.get("END_STEP", "5"))
    print(
        f"{EXPERIMENT}: {len(VARIANTS)} implementations x "
        f"{len(FLOW_COUNTS)} flow loads x {len(CONDITIONS)} conditions x "
        f"{len(RUNS)} runs = {expected_simulation_count()} simulations"
    )
    steps = [
        ("generate matched dynamic scenarios and INIs", generate_inputs),
        ("run simulations", lambda: run_simulations(cores)),
        ("export scavetool CSVs", lambda: export_csvs(cores)),
        ("extract plotting CSVs", lambda: extract_csvs(cores)),
        ("plot whole-run CDFs and parameter trade-offs", plot),
    ]

    for index, (name, function) in enumerate(steps, start=1):
        if start_step <= index <= end_step:
            print(f"Experiment Tuning Dynamic step {index}: {name}")
            function()
        else:
            print(f"Skipping Experiment Tuning Dynamic step {index}: {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
