#!/usr/bin/env python3

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import fnmatch
import os
from pathlib import Path
import subprocess
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent))

from experimentSensitivityAnalysisSupport import (  # noqa: E402
    EXPERIMENT,
    INI_FILE,
    RUNS,
    cases,
    expected_simulation_count,
)
from raynetExperimentSupport import (  # noqa: E402
    collect_simulation_configs,
    run_simulation_configs,
    select_experiment_protocols,
)


EXPERIMENT_DIR = (SCRIPT_DIR / "../../paperExperiments" / EXPERIMENT).resolve()
CONFIG_FILTER_ENV = "SENSITIVITY_CONFIG_FILTER"
PROTOCOLS = tuple(select_experiment_protocols(("orbtcp_pint",)))


def run_checked(command: list[str], cwd: Path) -> None:
    print(" ".join(str(part) for part in command))
    subprocess.run(command, cwd=cwd, check=True)


def run_parallel(
    commands: list[tuple[str, list[str]]], cwd: Path, workers: int
) -> None:
    def execute(label: str, command: list[str]) -> str:
        print(f"Starting {label}")
        subprocess.run(command, cwd=cwd, check=True)
        return label

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(execute, label, command): label
            for label, command in commands
        }
        try:
            for future in as_completed(futures):
                print(f"Completed {future.result()}")
        except BaseException:
            for future in futures:
                future.cancel()
            raise


def generate_inputs() -> None:
    for script in (
        "generateSensitivityCalibration.py",
        "generateExperimentSensitivityAnalysisScenarios.py",
        "generateExperimentSensitivityAnalysisIniFile.py",
    ):
        run_checked([sys.executable, script], SCRIPT_DIR)


def selected_cases():
    all_cases = list(cases())
    pattern = os.environ.get(CONFIG_FILTER_ENV, "").strip()
    if not pattern:
        return all_cases

    selected = [
        case
        for case in all_cases
        if fnmatch.fnmatchcase(case.config_name, pattern)
    ]
    if not selected:
        raise RuntimeError(
            f"{CONFIG_FILTER_ENV}={pattern!r} matched no configurations"
        )
    return selected


def simulation_configs():
    configs = collect_simulation_configs(
        PROTOCOLS[0], INI_FILE, RUNS, EXPERIMENT_DIR
    )
    expected = {case.config_name for case in cases()}
    found = {config.config_name for config in configs}
    if found != expected:
        missing = sorted(expected - found)
        unexpected = sorted(found - expected)
        raise RuntimeError(
            f"Unexpected {EXPERIMENT} configs: missing={missing}, "
            f"unexpected={unexpected}"
        )
    if len(configs) != expected_simulation_count():
        raise RuntimeError(
            f"Expected {expected_simulation_count()} configs, found {len(configs)}"
        )
    selected_names = {case.config_name for case in selected_cases()}
    return [config for config in configs if config.config_name in selected_names]


def run_simulations(cores: int) -> None:
    (EXPERIMENT_DIR / "results").mkdir(parents=True, exist_ok=True)
    runtime_file = SCRIPT_DIR / "experimentSensitivityAnalysisRunTimes.txt"
    runtime_file.unlink(missing_ok=True)
    with runtime_file.open("w", encoding="utf-8") as output:
        output.write("-- Experiment Sensitivity Analysis Runtimes (s) --\n")
        run_simulation_configs(
            simulation_configs(), EXPERIMENT_DIR, cores, output
        )


def expected_vec_files():
    for case in selected_cases():
        yield case, EXPERIMENT_DIR / "results" / f"{case.config_name}-#0.vec"


def export_csvs(cores: int) -> None:
    commands = []
    for case, vec_file in expected_vec_files():
        if not vec_file.is_file() or vec_file.stat().st_size == 0:
            raise FileNotFoundError(f"Missing simulation output: {vec_file}")
        csv_name = f"{case.config_name}.csv"
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
    run_parallel(commands, EXPERIMENT_DIR, cores)


def extract_csvs(cores: int) -> None:
    commands = []
    for case in selected_cases():
        csv_file = EXPERIMENT_DIR / "results" / f"{case.config_name}.csv"
        if not csv_file.is_file() or csv_file.stat().st_size == 0:
            raise FileNotFoundError(f"Missing exported CSV: {csv_file}")
        commands.append(
            (
                f"extract {case.config_name}",
                [
                    sys.executable,
                    "extractSingleCsvFile.py",
                    str(csv_file),
                    case.workload.experiment_key,
                    case.variant.key,
                    case.condition.key,
                    case.workload.key,
                    str(case.run),
                ],
            )
        )
    run_parallel(commands, SCRIPT_DIR, cores)


def plot() -> None:
    run_checked([sys.executable, "plotExperimentSensitivityAnalysis.py"], SCRIPT_DIR)


def main() -> int:
    cores = max(
        1,
        int(os.environ.get("EXPERIMENT_CORES", str(os.cpu_count() or 1))),
    )
    start_step = int(os.environ.get("START_STEP", "1"))
    end_step = int(os.environ.get("END_STEP", "5"))
    selected_count = len(selected_cases())
    print(f"Protocols: {list(PROTOCOLS)}")
    print(
        f"{EXPERIMENT}: {selected_count}/{expected_simulation_count()} "
        f"matched simulations; "
        f"up to {cores} concurrent workers"
    )
    steps = [
        ("generate calibration data, matched scenarios, and INI", generate_inputs),
        ("run simulations", lambda: run_simulations(cores)),
        ("export scavetool CSVs", lambda: export_csvs(cores)),
        ("extract plotting CSVs", lambda: extract_csvs(cores)),
        ("plot all sensitivity figures", plot),
    ]
    for index, (name, function) in enumerate(steps, start=1):
        if start_step <= index <= end_step:
            print(f"Sensitivity Analysis step {index}: {name}")
            function()
        else:
            print(f"Skipping Sensitivity Analysis step {index}: {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
