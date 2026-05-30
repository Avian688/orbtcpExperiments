#!/usr/bin/env python3

import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from raynetExperimentSupport import build_simulation_command


EXPERIMENT = "experiment0"
PROTOCOL = "bbr3"
INI_FILE = "experiment0_bbr3.ini"
RUNS = 5
VARIANTS = [
    ("no_updated_sack_no_pacing_no_rack", "Bbr3_NoUpdatedSackNoPacingNoRack"),
    ("updated_sack_no_pacing_no_rack", "Bbr3_UpdatedSackNoPacingNoRack"),
    ("updated_sack_pacing_no_rack", "Bbr3_UpdatedSackPacingNoRack"),
    ("all_enabled", "Bbr3_AllEnabled"),
]

SCRIPT_DIR = Path(__file__).resolve().parent
EXPERIMENT_DIR = (SCRIPT_DIR / "../../paperExperiments" / EXPERIMENT).resolve()


def run_checked(command, cwd: Path) -> None:
    print(" ".join(str(part) for part in command))
    subprocess.run(command, cwd=cwd, check=True)


def batched(commands, cwd: Path, cores: int) -> None:
    active: list[tuple[str, subprocess.Popen]] = []
    for label, command in commands:
        print(f"Starting {label}")
        active.append((label, subprocess.Popen(command, cwd=cwd)))
        if len(active) >= cores:
            wait_for_batch(active)
            active.clear()
    wait_for_batch(active)


def wait_for_batch(active: list[tuple[str, subprocess.Popen]]) -> None:
    failures = []
    for label, process in active:
        status = process.wait()
        if status == 0:
            print(f"Completed {label}")
        else:
            failures.append((label, status))
            print(f"FAILED {label} with exit code {status}")
    if failures:
        failed = ", ".join(f"{label}={status}" for label, status in failures)
        raise RuntimeError(f"Experiment 0 batch failed: {failed}")


def generate_inputs() -> None:
    run_checked([sys.executable, "generateExperiment0Scenarios.py"], SCRIPT_DIR)
    run_checked([sys.executable, "generateExperiment0IniFile.py"], SCRIPT_DIR)


def simulation_commands() -> list[tuple[str, list[str]]]:
    commands = []
    for variant_key, config_prefix in VARIANTS:
        for run in range(1, RUNS + 1):
            config_name = f"{config_prefix}_Run{run}"
            label = f"{variant_key} run{run}"
            commands.append((label, build_simulation_command(PROTOCOL, INI_FILE, config_name)))
    return commands


def expected_vec_files() -> list[Path]:
    return [
        EXPERIMENT_DIR / "results" / f"{config_prefix}_Run{run}-#0.vec"
        for _, config_prefix in VARIANTS
        for run in range(1, RUNS + 1)
    ]


def run_simulations(cores: int) -> None:
    (EXPERIMENT_DIR / "results").mkdir(parents=True, exist_ok=True)
    batched(simulation_commands(), EXPERIMENT_DIR, cores)
    missing = [path for path in expected_vec_files() if not path.is_file()]
    if missing:
        print("Missing vec files after first pass, retrying missing configs:")
        retry = []
        for path in missing:
            stem = path.name.removesuffix("-#0.vec")
            print(f"  {path.name}")
            retry.append((stem, build_simulation_command(PROTOCOL, INI_FILE, stem)))
        batched(retry, EXPERIMENT_DIR, cores)


def export_csvs(cores: int) -> None:
    commands = []
    for vec_path in expected_vec_files():
        csv_name = vec_path.name.removesuffix(".vec") + ".csv"
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
                    str(Path("results") / vec_path.name),
                ],
            )
        )
    batched(commands, EXPERIMENT_DIR, cores)


def extract_csvs(cores: int) -> None:
    commands = []
    for variant_key, config_prefix in VARIANTS:
        for run in range(1, RUNS + 1):
            csv_file = EXPERIMENT_DIR / "results" / f"{config_prefix}_Run{run}-#0.csv"
            if not csv_file.is_file():
                print(f"Skipping missing CSV {csv_file}")
                continue
            commands.append(
                (
                    f"extract {variant_key} run{run}",
                    [sys.executable, "extractSingleCsvFile.py", str(csv_file), variant_key, str(run)],
                )
            )
    batched(commands, SCRIPT_DIR, cores)


def plot() -> None:
    run_checked([sys.executable, "plotCwndComparison.py"], SCRIPT_DIR)


def main() -> int:
    cores = max(1, int(os.environ.get("EXPERIMENT_CORES", "1")))
    start_step = int(os.environ.get("EXPERIMENT_START_STEP", "1"))
    end_step = int(os.environ.get("EXPERIMENT_END_STEP", "5"))

    steps = [
        ("generate ini/scenarios", generate_inputs),
        ("run simulations", lambda: run_simulations(cores)),
        ("export scavetool CSVs", lambda: export_csvs(cores)),
        ("extract CWND CSVs", lambda: extract_csvs(cores)),
        ("plot CWND comparisons", plot),
    ]

    for index, (name, fn) in enumerate(steps, start=1):
        if start_step <= index <= end_step:
            print(f"Experiment 0 step {index}: {name}")
            fn()
        else:
            print(f"Skipping experiment 0 step {index}: {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
