#!/usr/bin/env python3

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from raynetExperimentSupport import select_experiment_protocols


EXPERIMENT = "experiment0"
INI_FILE = "experiment0_bbr3.ini"
RUNS = 5
EXPERIMENT0_NED_PATHS = (
    "../..",
    "../../../src",
    "../../../../bbr/simulations",
    "../../../../bbr/src",
    "../../../../inet4.5/examples",
    "../../../../inet4.5/showcases",
    "../../../../inet4.5/src",
    "../../../../inet4.5/tests/validation",
    "../../../../inet4.5/tests/networks",
    "../../../../inet4.5/tutorials",
    "../../../../tcpPaced/src",
    "../../../../tcpPaced/simulations",
    "../../../../tcpGoodputApplications/simulations",
    "../../../../tcpGoodputApplications/src",
)
EXPERIMENT0_LIBS = (
    "../../../../inet4.5/src/INET",
    "../../../../tcpPaced/src/tcpPaced",
    "../../../../tcpGoodputApplications/src/tcpGoodputApplications",
    "../../../../bbr/src/bbr",
    "../../../src/orbtcpExperiments",
)
LIBRARY_REBUILD_ORDER = (
    "inet4.5",
    "tcpPaced",
    "tcpGoodputApplications",
    "bbr",
    "orbtcpExperiments",
)
LIBRARY_DEPENDENCIES = (
    ("tcpPaced", "INET"),
    ("tcpGoodputApplications", "INET"),
    ("bbr", "INET"),
    ("bbr", "tcpPaced"),
    ("orbtcpExperiments", "INET"),
)
PROTOCOL_CONFIGS = {
    "bbr3": "Bbr3",
    "cubic": "Cubic",
    "bbr": "Bbr",
}
SELECTED_PROTOCOLS = select_experiment_protocols(PROTOCOL_CONFIGS)
PROTOCOLS = [
    (protocol, PROTOCOL_CONFIGS[protocol]) for protocol in SELECTED_PROTOCOLS
]
VARIANTS = [
    ("no_updated_sack_no_pacing_no_rack", "NoUpdatedSackNoPacingNoRack"),
    ("updated_sack_no_pacing_no_rack", "UpdatedSackNoPacingNoRack"),
    ("updated_sack_pacing_no_rack", "UpdatedSackPacingNoRack"),
    ("all_enabled", "AllEnabled"),
]

SCRIPT_DIR = Path(__file__).resolve().parent
EXPERIMENT_DIR = (SCRIPT_DIR / "../../paperExperiments" / EXPERIMENT).resolve()


def library_base_name(lib_path: str) -> str:
    return Path(lib_path).name


def resolve_library_file(lib_path: str) -> Path | None:
    path = (EXPERIMENT_DIR / lib_path).resolve()
    parent = path.parent
    name = path.name
    candidates = [
        parent / f"lib{name}.so",
        parent / f"lib{name}_dbg.so",
        parent / f"lib{name}.dylib",
        parent / f"lib{name}_dbg.dylib",
    ]
    existing = [candidate for candidate in candidates if candidate.is_file()]
    return max(existing, key=lambda candidate: candidate.stat().st_mtime) if existing else None


def check_library_freshness() -> None:
    if os.environ.get("EXPERIMENT0_SKIP_BUILD_CHECK", "").lower() in {"1", "true", "yes", "on"}:
        return

    libraries = {
        library_base_name(lib_path): resolve_library_file(lib_path)
        for lib_path in EXPERIMENT0_LIBS
    }
    missing = [name for name, path in libraries.items() if path is None]
    if missing:
        print("WARNING: Could not find built shared libraries for: " + ", ".join(missing))
        return

    stale = []
    for dependent, dependency in LIBRARY_DEPENDENCIES:
        dependent_path = libraries.get(dependent)
        dependency_path = libraries.get(dependency)
        if dependent_path is None or dependency_path is None:
            continue
        if dependent_path.stat().st_mtime + 1 < dependency_path.stat().st_mtime:
            stale.append((dependent, dependent_path, dependency, dependency_path))

    if not stale:
        return

    print("Experiment 0 shared-library freshness check failed.")
    print("This commonly causes Linux-only vtable/typeinfo segfaults when a dependent project was not rebuilt.")
    for dependent, dependent_path, dependency, dependency_path in stale:
        print(
            f"  {dependent_path} is older than {dependency_path} "
            f"({dependent} depends on {dependency})"
        )
    print("Rebuild in this order from the samples folder:")
    for project in LIBRARY_REBUILD_ORDER:
        print(f"  (cd {project} && make)")
    print("If you intentionally want to bypass this check, set EXPERIMENT0_SKIP_BUILD_CHECK=1.")
    raise RuntimeError("stale experiment 0 shared libraries")


def run_checked(command, cwd: Path) -> None:
    print(" ".join(str(part) for part in command))
    subprocess.run(command, cwd=cwd, check=True)


def batched(commands, cwd: Path, cores: int, log_dir: Path | None = None) -> None:
    active: list[tuple[str, subprocess.Popen, object | None, Path | None]] = []
    remaining = iter(commands)
    failures = []
    cores = max(1, cores)
    if log_dir is not None:
        log_dir.mkdir(parents=True, exist_ok=True)

    while True:
        while len(active) < cores:
            try:
                label, command = next(remaining)
            except StopIteration:
                break
            print(f"Starting {label}")
            log_file = None
            log_path = None
            output_kwargs = {
                "stdout": subprocess.DEVNULL,
                "stderr": subprocess.DEVNULL,
            }
            if log_dir is not None:
                safe_label = label.replace("/", "_").replace(" ", "_")
                log_path = log_dir / f"{safe_label}.log"
                log_file = log_path.open("w", encoding="utf-8")
                log_file.write("$ " + " ".join(command) + "\n\n")
                log_file.flush()
                output_kwargs = {
                    "stdout": log_file,
                    "stderr": subprocess.STDOUT,
                }

            try:
                process = subprocess.Popen(command, cwd=cwd, **output_kwargs)
            except BaseException:
                if log_file is not None:
                    log_file.close()
                raise
            active.append(
                (label, process, log_file, log_path)
            )

        if not active:
            break

        completed = [entry for entry in active if entry[1].poll() is not None]
        if not completed:
            time.sleep(0.05)
            continue

        for label, process, log_file, log_path in completed:
            active.remove((label, process, log_file, log_path))
            status = process.returncode
            if log_file is not None:
                log_file.write(f"\nExit code: {status}\n")
                log_file.close()
            if status == 0:
                print(f"Completed {label}")
            else:
                failures.append((label, status))
                print(f"FAILED {label} with exit code {status}")
                if log_path is not None:
                    print(f"  log: {log_path}")

    if failures:
        failed = ", ".join(f"{label}={status}" for label, status in failures)
        raise RuntimeError(f"Experiment 0 simulation run failed: {failed}")


def generate_inputs() -> None:
    run_checked([sys.executable, "generateExperiment0Scenarios.py"], SCRIPT_DIR)
    run_checked([sys.executable, "generateExperiment0IniFile.py"], SCRIPT_DIR)


def build_experiment0_command(config_name: str) -> list[str]:
    command = [
        "opp_run",
        "-r",
        "0",
        "-m",
        "-u",
        "Cmdenv",
        "-c",
        config_name,
        "-n",
        ":".join(EXPERIMENT0_NED_PATHS),
        "--image-path=../../../../inet4.5/images",
        "--*.visualizer.typename=\"\"",
    ]
    for lib in EXPERIMENT0_LIBS:
        command.extend(["-l", lib])
    command.append(INI_FILE)
    return command


def experiment_cases():
    for protocol_key, protocol_config in PROTOCOLS:
        for variant_key, variant_config in VARIANTS:
            yield f"{protocol_key}/{variant_key}", f"{protocol_config}_{variant_config}"


def simulation_commands() -> list[tuple[str, list[str]]]:
    commands = []
    for case_key, config_prefix in experiment_cases():
        for run in range(1, RUNS + 1):
            config_name = f"{config_prefix}_Run{run}"
            label = f"{case_key} run{run}"
            commands.append((label, build_experiment0_command(config_name)))
    return commands


def expected_vec_files() -> list[Path]:
    return [
        EXPERIMENT_DIR / "results" / f"{config_prefix}_Run{run}-#0.vec"
        for _, config_prefix in experiment_cases()
        for run in range(1, RUNS + 1)
    ]


def run_simulations(cores: int) -> None:
    check_library_freshness()
    (EXPERIMENT_DIR / "results").mkdir(parents=True, exist_ok=True)
    retry_log_dir = EXPERIMENT_DIR.parents[1] / "logs" / "experiment0" / "simulations"
    if retry_log_dir.is_dir():
        for stale_log in retry_log_dir.glob("*.log"):
            stale_log.unlink(missing_ok=True)
    batched(simulation_commands(), EXPERIMENT_DIR, cores)
    missing = [path for path in expected_vec_files() if not path.is_file()]
    if missing:
        print("Missing vec files after first pass, retrying missing configs:")
        retry = []
        for path in missing:
            stem = path.name.removesuffix("-#0.vec")
            print(f"  {path.name}")
            retry.append((stem, build_experiment0_command(stem)))
        batched(retry, EXPERIMENT_DIR, cores, log_dir=retry_log_dir)


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
    for case_key, config_prefix in experiment_cases():
        for run in range(1, RUNS + 1):
            csv_file = EXPERIMENT_DIR / "results" / f"{config_prefix}_Run{run}-#0.csv"
            if not csv_file.is_file():
                print(f"Skipping missing CSV {csv_file}")
                continue
            commands.append(
                (
                    f"extract {case_key} run{run}",
                    [sys.executable, "extractSingleCsvFile.py", str(csv_file), case_key, str(run)],
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
        ("extract CWND/goodput CSVs", lambda: extract_csvs(cores)),
        ("plot CWND/goodput comparisons", plot),
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
