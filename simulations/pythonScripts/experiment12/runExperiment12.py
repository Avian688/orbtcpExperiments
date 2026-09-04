#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
import os
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from raynetExperimentSupport import (
    collect_simulation_configs,
    protocol_config_prefix,
    run_simulation_configs,
    select_experiment_protocols,
)


EXPERIMENT = "experiment12"
PROTOCOLS = tuple(select_experiment_protocols(("cubic", "bbr")))
RUNS = range(1, 6)
SCRIPT_DIR = Path(__file__).resolve().parent
EXPERIMENT_DIR = (SCRIPT_DIR / "../../paperExperiments" / EXPERIMENT).resolve()
PLOT_DIR = (SCRIPT_DIR / "../../plots" / EXPERIMENT / "cumulative").resolve()


def run_checked(command, cwd: Path) -> None:
    print(" ".join(str(part) for part in command))
    subprocess.run(command, cwd=cwd, check=True)


def batched(commands, cwd: Path, cores: int) -> None:
    active = []
    for label, command in commands:
        print(f"Starting {label}")
        active.append((label, subprocess.Popen(command, cwd=cwd)))
        if len(active) >= cores:
            wait_for_batch(active)
            active.clear()
    wait_for_batch(active)


def wait_for_batch(active) -> None:
    failed = []
    for label, process in active:
        status = process.wait()
        if status == 0:
            print(f"Completed {label}")
        else:
            failed.append(f"{label}={status}")
    if failed:
        raise RuntimeError("Experiment 12 batch failed: " + ", ".join(failed))


def config_name(protocol: str, run: int) -> str:
    return f"{protocol_config_prefix(protocol)}_Run{run}"


def generate_inputs() -> None:
    run_checked([sys.executable, "generateExperiment12Scenarios.py"], SCRIPT_DIR)
    run_checked([sys.executable, "generateExperiment12IniFile.py"], SCRIPT_DIR)


def run_simulations(cores: int) -> None:
    (EXPERIMENT_DIR / "results").mkdir(parents=True, exist_ok=True)
    runtime_file = SCRIPT_DIR / "experiment12runTimes.txt"
    runtime_file.unlink(missing_ok=True)
    with runtime_file.open("w", encoding="utf-8") as output:
        output.write("--Experiment 12 Runtimes (s)--")
        simulation_configs = []
        for protocol in PROTOCOLS:
            ini_name = f"experiment12_{protocol}.ini"
            configs = collect_simulation_configs(protocol, ini_name, RUNS, EXPERIMENT_DIR)
            if len(configs) != len(RUNS):
                raise RuntimeError(f"Expected {len(RUNS)} configs in {ini_name}, found {len(configs)}")
            simulation_configs.extend(configs)
        run_simulation_configs(simulation_configs, EXPERIMENT_DIR, cores, output)


def expected_vec_files():
    return [
        EXPERIMENT_DIR / "results" / f"{config_name(protocol, run)}-#0.vec"
        for protocol in PROTOCOLS
        for run in RUNS
    ]


def export_csvs(cores: int) -> None:
    commands = []
    for vec_file in expected_vec_files():
        if not vec_file.is_file():
            raise FileNotFoundError(f"Missing simulation output: {vec_file}")
        csv_file = vec_file.with_name(vec_file.name.removesuffix("-#0.vec") + ".csv")
        commands.append(
            (
                csv_file.name,
                [
                    "opp_scavetool",
                    "export",
                    "-o",
                    str(Path("results") / csv_file.name),
                    "-F",
                    "CSV-R",
                    str(Path("results") / vec_file.name),
                ],
            )
        )
    batched(commands, EXPERIMENT_DIR, cores)


def extract_csvs(cores: int) -> None:
    commands = []
    for protocol in PROTOCOLS:
        for run in RUNS:
            csv_file = EXPERIMENT_DIR / "results" / f"{config_name(protocol, run)}.csv"
            if not csv_file.is_file():
                raise FileNotFoundError(f"Missing exported CSV: {csv_file}")
            commands.append(
                (
                    f"extract {protocol} run{run}",
                    [sys.executable, "extractSingleCsvFile.py", str(csv_file), protocol, str(run)],
                )
            )
    batched(commands, SCRIPT_DIR, cores)


def plot() -> None:
    PLOT_DIR.mkdir(parents=True, exist_ok=True)
    run_checked(
        [
            sys.executable,
            str(SCRIPT_DIR.parent / "runPlotVariants.py"),
            str(SCRIPT_DIR / "plotScatterEfficiency.py"),
        ],
        PLOT_DIR,
    )


def main() -> int:
    cores = max(1, int(os.environ.get("EXPERIMENT_CORES", "1")))
    start_step = int(os.environ.get("START_STEP", "1"))
    end_step = int(os.environ.get("END_STEP", "5"))
    steps = [
        ("generate scenarios and ini files", generate_inputs),
        ("run simulations", lambda: run_simulations(cores)),
        ("export scavetool CSVs", lambda: export_csvs(cores)),
        ("extract plotting CSVs", lambda: extract_csvs(cores)),
        ("plot aggregate efficiency scatter", plot),
    ]

    for index, (name, function) in enumerate(steps, start=1):
        if start_step <= index <= end_step:
            print(f"Experiment 12 step {index}: {name}")
            function()
        else:
            print(f"Skipping experiment 12 step {index}: {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
