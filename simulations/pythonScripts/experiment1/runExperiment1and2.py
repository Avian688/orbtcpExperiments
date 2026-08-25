#!/usr/bin/env python3

# Runs experiment 1 and experiment 2.
# The runner verifies every expected output before moving to the next stage so
# high-parallelism runs cannot silently skip failed or missing processes.

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from raynetExperimentSupport import build_simulation_command, with_experiment_protocols


SCRIPT_DIR = Path(__file__).resolve().parent
SIM_ROOT = SCRIPT_DIR.parent.parent
PAPER_ROOT = SIM_ROOT / "paperExperiments"
PLOTS_ROOT = SIM_ROOT / "plots"
LOG_ROOT = SIM_ROOT / "logs" / "experiment1and2"


@dataclass(frozen=True)
class ConfigEntry:
    experiment: str
    protocol: str
    ini_name: str
    config_name: str
    run: int


def parse_args() -> argparse.Namespace:
    default_cores = int(
        os.environ.get(
            "EXPERIMENT_CORES",
            os.environ.get("ORBTCP_EXPERIMENT_CORES", str(os.cpu_count() or 1)),
        )
    )
    parser = argparse.ArgumentParser(description="Run or plot orbtcpExperiments experiment 1 and 2.")
    parser.add_argument("--cores", type=int, default=max(1, default_cores), help="Maximum parallel child processes.")
    parser.add_argument("--retries", type=int, default=int(os.environ.get("EXPERIMENT_RETRIES", "3")))
    parser.add_argument("--start-step", type=int, default=int(os.environ.get("START_STEP", "1")))
    parser.add_argument("--end-step", type=int, default=int(os.environ.get("END_STEP", "10")))
    parser.add_argument("--runs", type=int, default=int(os.environ.get("EXPERIMENT_RUNS", "50")))
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Skip simulations whose expected vector file already exists.",
    )
    return parser.parse_args()


def step_enabled(curr_step: int, args: argparse.Namespace) -> bool:
    return args.start_step <= curr_step <= args.end_step


def run_checked(command: list[str], cwd: Path, description: str, timeout: int | None = None) -> None:
    print(description)
    result = subprocess.run(command, cwd=str(cwd), timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError(f"{description} failed with exit code {result.returncode}")


def collect_config_entries(experiment: str, protocols: list[str], run_list: list[int]) -> list[ConfigEntry]:
    config_entries: list[ConfigEntry] = []
    run_re = re.compile(r"Run(\d{1,5})\]")

    for protocol in protocols:
        ini_name = f"{experiment}_{protocol}.ini"
        ini_path = PAPER_ROOT / experiment / ini_name
        if not ini_path.exists():
            raise FileNotFoundError(f"Missing ini file: {ini_path}")

        for line in ini_path.read_text(encoding="utf-8").splitlines():
            if not line.startswith("[Config "):
                continue
            match = run_re.search(line)
            if not match:
                continue
            run = int(match.group(1))
            if run not in run_list:
                continue
            config_name = line[len("[Config ") : -1]
            config_entries.append(ConfigEntry(experiment, protocol, ini_name, config_name, run))

    return config_entries


def result_dir(entry: ConfigEntry) -> Path:
    return PAPER_ROOT / entry.experiment / "results"


def matching_vec_files(entry: ConfigEntry) -> list[Path]:
    return sorted(result_dir(entry).glob(f"{entry.config_name}*.vec"))


def expected_csv_path(entry: ConfigEntry) -> Path:
    return result_dir(entry) / f"{entry.config_name}.csv"


def clean_result_files(entry: ConfigEntry) -> None:
    for suffix in ("-#0.vec", "-#0.vci", "-#0.sca", ".csv"):
        (result_dir(entry) / f"{entry.config_name}{suffix}").unlink(missing_ok=True)


def retry_log_path(log_dir: Path, config_name: str, attempt: int) -> Path | None:
    if attempt == 1:
        if log_dir.is_dir():
            for stale_log in log_dir.glob(f"{config_name}.attempt*.log"):
                stale_log.unlink(missing_ok=True)
        return None

    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / f"{config_name}.attempt{attempt}.log"


def run_with_retry_logging(
    command: list[str], cwd: Path, log_path: Path | None
) -> subprocess.CompletedProcess:
    if log_path is None:
        return subprocess.run(
            command,
            cwd=str(cwd),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    started = time.time()
    with log_path.open("w", encoding="utf-8") as log_file:
        log_file.write("$ " + " ".join(command) + "\n\n")
        log_file.flush()
        result = subprocess.run(
            command,
            cwd=str(cwd),
            stdout=log_file,
            stderr=subprocess.STDOUT,
        )
        log_file.write(f"\nExit code: {result.returncode}\n")
        log_file.write(f"Elapsed seconds: {time.time() - started:.2f}\n")
    return result


def log_status(log_path: Path | None) -> str:
    return (
        f"log: {log_path}"
        if log_path is not None
        else "first-attempt output suppressed; retry will be logged"
    )


def run_single_simulation(
    entry: ConfigEntry, attempt: int, resume: bool
) -> tuple[ConfigEntry, bool, int, Path | None]:
    result_dir(entry).mkdir(parents=True, exist_ok=True)
    if resume and matching_vec_files(entry):
        return entry, True, 0, None

    clean_result_files(entry)
    log_dir = LOG_ROOT / entry.experiment / entry.protocol / "simulations"
    log_path = retry_log_path(log_dir, entry.config_name, attempt)
    command = build_simulation_command(entry.protocol, entry.ini_name, entry.config_name)
    result = run_with_retry_logging(
        command, PAPER_ROOT / entry.experiment, log_path
    )

    ok = result.returncode == 0 and bool(matching_vec_files(entry))
    return entry, ok, result.returncode, log_path


def run_simulations(entries: list[ConfigEntry], args: argparse.Namespace) -> None:
    pending = list(entries)
    total_attempts = args.retries + 1

    for attempt in range(1, total_attempts + 1):
        if not pending:
            return

        print(
            f"\nRunning {len(pending)} simulation config(s), attempt {attempt}/{total_attempts}, "
            f"using {args.cores} core(s).\n"
        )
        failed: list[ConfigEntry] = []

        with ThreadPoolExecutor(max_workers=args.cores) as executor:
            futures = {
                executor.submit(run_single_simulation, entry, attempt, args.resume and attempt == 1): entry
                for entry in pending
            }
            for future in as_completed(futures):
                entry, ok, return_code, log_path = future.result()
                if ok:
                    print(f"  complete: {entry.config_name}")
                else:
                    failed.append(entry)
                    print(
                        f"  failed/missing vec: {entry.config_name} "
                        f"(exit {return_code}, {log_status(log_path)})"
                    )

        pending = failed
        if pending and attempt < total_attempts:
            print(f"\nRetrying {len(pending)} missing/failed config(s).\n")

    missing = "\n".join(f"  {entry.experiment}: {entry.config_name}" for entry in pending)
    raise RuntimeError(f"Simulation outputs are still missing after retries:\n{missing}")


def csv_name_for_vec(vec_file: Path) -> str:
    name = vec_file.name
    if name.endswith("-#0.vec"):
        return name[:-7] + ".csv"
    return vec_file.stem + ".csv"


def export_single_csv(
    entry: ConfigEntry, attempt: int
) -> tuple[ConfigEntry, bool, int, Path | None]:
    vec_files = matching_vec_files(entry)
    if not vec_files:
        return entry, False, 127, None

    vec_file = vec_files[0]
    csv_name = csv_name_for_vec(vec_file)
    csv_path = result_dir(entry) / csv_name
    csv_path.unlink(missing_ok=True)

    log_dir = LOG_ROOT / entry.experiment / entry.protocol / "scavetool"
    log_path = retry_log_path(log_dir, entry.config_name, attempt)
    command = [
        "opp_scavetool",
        "export",
        "-o",
        f"results/{csv_name}",
        "-F",
        "CSV-R",
        f"results/{vec_file.name}",
    ]

    result = run_with_retry_logging(
        command, PAPER_ROOT / entry.experiment, log_path
    )

    ok = result.returncode == 0 and csv_path.exists()
    return entry, ok, result.returncode, log_path


def export_csvs(entries: list[ConfigEntry], args: argparse.Namespace) -> None:
    pending = list(entries)
    total_attempts = args.retries + 1

    for attempt in range(1, total_attempts + 1):
        if not pending:
            return

        print(
            f"\nExporting {len(pending)} vector file(s) to CSV, attempt {attempt}/{total_attempts}, "
            f"using {args.cores} core(s).\n"
        )
        failed: list[ConfigEntry] = []

        with ThreadPoolExecutor(max_workers=args.cores) as executor:
            futures = {executor.submit(export_single_csv, entry, attempt): entry for entry in pending}
            for future in as_completed(futures):
                entry, ok, return_code, log_path = future.result()
                if ok:
                    print(f"  csv complete: {entry.config_name}")
                else:
                    failed.append(entry)
                    print(
                        f"  csv failed/missing: {entry.config_name} "
                        f"(exit {return_code}, {log_status(log_path)})"
                    )

        pending = failed

    missing = "\n".join(f"  {entry.experiment}: {entry.config_name}" for entry in pending)
    raise RuntimeError(f"CSV exports are still missing after retries:\n{missing}")


def extracted_run_dir(entry: ConfigEntry) -> Path:
    return PAPER_ROOT / entry.experiment / "csvs" / entry.protocol / f"run{entry.run}"


def has_extracted_data(entry: ConfigEntry) -> bool:
    run_dir = extracted_run_dir(entry)
    return run_dir.is_dir() and any(run_dir.rglob("*.csv"))


def extract_single_csv(
    entry: ConfigEntry, attempt: int
) -> tuple[ConfigEntry, bool, int, Path | None]:
    csv_path = expected_csv_path(entry)
    if not csv_path.exists():
        return entry, False, 127, None

    shutil.rmtree(extracted_run_dir(entry), ignore_errors=True)

    log_dir = LOG_ROOT / entry.experiment / entry.protocol / "extract"
    log_path = retry_log_path(log_dir, entry.config_name, attempt)
    command = [
        sys.executable,
        "extractSingleCsvFile.py",
        str(csv_path),
        entry.experiment,
        entry.protocol,
        str(entry.run),
    ]

    result = run_with_retry_logging(command, SCRIPT_DIR, log_path)

    ok = result.returncode == 0 and has_extracted_data(entry)
    return entry, ok, result.returncode, log_path


def extract_csvs(entries: list[ConfigEntry], args: argparse.Namespace) -> None:
    pending = list(entries)
    total_attempts = args.retries + 1

    for attempt in range(1, total_attempts + 1):
        if not pending:
            return

        print(
            f"\nExtracting {len(pending)} CSV result file(s), attempt {attempt}/{total_attempts}, "
            f"using {args.cores} core(s).\n"
        )
        failed: list[ConfigEntry] = []

        with ThreadPoolExecutor(max_workers=args.cores) as executor:
            futures = {executor.submit(extract_single_csv, entry, attempt): entry for entry in pending}
            for future in as_completed(futures):
                entry, ok, return_code, log_path = future.result()
                if ok:
                    print(f"  extract complete: {entry.config_name}")
                else:
                    failed.append(entry)
                    print(
                        f"  extract failed/missing: {entry.config_name} "
                        f"(exit {return_code}, {log_status(log_path)})"
                    )

        pending = failed

    missing = "\n".join(f"  {entry.experiment}: {entry.config_name}" for entry in pending)
    raise RuntimeError(f"CSV extraction outputs are still missing after retries:\n{missing}")


def plot_input_paths(entry: ConfigEntry) -> list[tuple[str, Path]]:
    run_dir = extracted_run_dir(entry)
    return [
        ("plotGoodput.py", run_dir / "singledumbbell.server[0].app[0]" / "goodput.csv"),
        ("plotThroughput.py", run_dir / "singledumbbell.server[0].tcp.conn" / "throughput.csv"),
        ("plotCwnd.py", run_dir / "singledumbbell.client[0].tcp.conn" / "cwnd.csv"),
        ("plotQueueLength.py", run_dir / "singledumbbell.router1.ppp[1].queue" / "queueLength.csv"),
        ("plotRtt.py", run_dir / "singledumbbell.client[0].tcp.conn" / "rtt.csv"),
        ("plotBytesInFlight.py", run_dir / "singledumbbell.client[0].tcp.conn" / "mbytesInFlight.csv"),
    ]


def plot_run_dir(entry: ConfigEntry) -> Path:
    return PLOTS_ROOT / entry.experiment / entry.protocol / f"run{entry.run}"


def prepare_plot_dirs(entries: list[ConfigEntry]) -> None:
    for experiment in sorted({entry.experiment for entry in entries}):
        shutil.rmtree(PLOTS_ROOT / experiment, ignore_errors=True)
        (PLOTS_ROOT / experiment).mkdir(parents=True, exist_ok=True)

    for entry in entries:
        plot_run_dir(entry).mkdir(parents=True, exist_ok=True)


def run_plot_task(script_name: str, csv_path: Path, cwd: Path) -> tuple[str, bool, int]:
    rel_csv = os.path.relpath(csv_path, cwd)
    result = subprocess.run([sys.executable, str(SCRIPT_DIR / script_name), rel_csv], cwd=str(cwd))
    return f"{cwd.name}/{script_name}", result.returncode == 0, result.returncode


def plot_individual_runs(entries: list[ConfigEntry], args: argparse.Namespace) -> None:
    missing_inputs: list[Path] = []
    tasks: list[tuple[str, Path, Path]] = []

    for entry in entries:
        cwd = plot_run_dir(entry)
        for script_name, csv_path in plot_input_paths(entry):
            if csv_path.exists():
                tasks.append((script_name, csv_path, cwd))
            else:
                missing_inputs.append(csv_path)

    if missing_inputs:
        sample = "\n".join(f"  {path}" for path in missing_inputs[:40])
        extra = "" if len(missing_inputs) <= 40 else f"\n  ... and {len(missing_inputs) - 40} more"
        raise RuntimeError(f"Cannot plot because expected extracted CSV inputs are missing:\n{sample}{extra}")

    print(f"\nPlotting {len(tasks)} per-run figure(s) using {args.cores} core(s).\n")
    failures: list[str] = []
    with ThreadPoolExecutor(max_workers=args.cores) as executor:
        futures = {executor.submit(run_plot_task, *task): task for task in tasks}
        for future in as_completed(futures):
            name, ok, return_code = future.result()
            if ok:
                print(f"  plot complete: {name}")
            else:
                failures.append(f"{name} (exit {return_code})")

    if failures:
        raise RuntimeError("Plotting failed:\n" + "\n".join(f"  {failure}" for failure in failures))

    print("\nMerging per-run PDFs.\n")
    merge_failures: list[str] = []
    with ThreadPoolExecutor(max_workers=args.cores) as executor:
        futures = {}
        for entry in entries:
            cwd = plot_run_dir(entry)
            futures[executor.submit(subprocess.run, [sys.executable, str(SCRIPT_DIR / "mergePdfs.py")], cwd=str(cwd))] = cwd
        for future in as_completed(futures):
            cwd = futures[future]
            result = future.result()
            if result.returncode != 0:
                merge_failures.append(f"{cwd} (exit {result.returncode})")

    if merge_failures:
        raise RuntimeError("PDF merging failed:\n" + "\n".join(f"  {failure}" for failure in merge_failures))


def plot_cumulative(script_name: str) -> None:
    cumulative_dir = PLOTS_ROOT / "experiment1and2Cumulative"
    cumulative_dir.mkdir(parents=True, exist_ok=True)
    run_checked(
        [
            sys.executable,
            str(SCRIPT_DIR.parent / "runPlotVariants.py"),
            str(SCRIPT_DIR / script_name),
        ],
        cwd=cumulative_dir,
        description=(
            f"Running {script_name} "
            "(final OrbCC main and full-INT diagnostic)"
        ),
        timeout=3600,
    )


def plot_protocol_legends() -> None:
    cumulative_dir = PLOTS_ROOT / "experiment1and2Cumulative"
    cumulative_dir.mkdir(parents=True, exist_ok=True)
    run_checked(
        [
            sys.executable,
            str(SCRIPT_DIR.parent / "runPlotVariants.py"),
            str(SCRIPT_DIR.parent / "plotHeaderLines.py"),
        ],
        cwd=cumulative_dir,
        description="Generating Experiment 1/2 standalone protocol legends",
        timeout=3600,
    )


def generate_inputs() -> None:
    run_checked([sys.executable, "generateExperiment1Scenarios.py"], SCRIPT_DIR, "Generating experiment 1 scenarios")
    run_checked([sys.executable, "generateExperiment1IniFile.py"], SCRIPT_DIR, "Generating experiment 1 ini files")
    run_checked(
        [sys.executable, "../experiment2/generateExperiment2Scenarios.py"],
        SCRIPT_DIR,
        "Generating experiment 2 scenarios",
    )
    run_checked(
        [sys.executable, "../experiment2/generateExperiment2IniFile.py"],
        SCRIPT_DIR,
        "Generating experiment 2 ini files",
    )


def clean_previous_csvs(protocols: list[str], experiments: list[str]) -> None:
    for experiment in experiments:
        (PAPER_ROOT / experiment / "results").mkdir(parents=True, exist_ok=True)
        for protocol in protocols:
            shutil.rmtree(PAPER_ROOT / experiment / "csvs" / protocol, ignore_errors=True)


def write_runtime_header(experiment: str) -> None:
    (SCRIPT_DIR / f"{experiment}runTimes.txt").write_text(
        f"--{experiment.title()} Runtimes (s)--\n",
        encoding="utf-8",
    )


def main() -> int:
    args = parse_args()
    os.chdir(SCRIPT_DIR)

    experiments = ["experiment1", "experiment2"]
    protocols = with_experiment_protocols(["orbtcp", "bbr", "cubic", "bbr3", "satcp", "leocc"])
    run_list = list(range(1, args.runs + 1))
    print(f"Protocols: {protocols}")
    print(f"Runs: 1-{args.runs}")
    print(f"Cores: {args.cores}")
    print(f"Retries: {args.retries}")

    curr_step = 1
    entries: list[ConfigEntry] = []

    if step_enabled(curr_step, args):
        generate_inputs()
        clean_previous_csvs(protocols, experiments)
        for experiment in experiments:
            write_runtime_header(experiment)
        entries = collect_config_entries("experiment1", protocols, run_list)
        run_simulations(entries, args)
    curr_step += 1

    if step_enabled(curr_step, args):
        if not entries:
            entries = collect_config_entries("experiment2", protocols, run_list)
        else:
            entries = collect_config_entries("experiment2", protocols, run_list)
        run_simulations(entries, args)
    curr_step += 1

    all_entries = collect_config_entries("experiment1", protocols, run_list) + collect_config_entries(
        "experiment2", protocols, run_list
    )

    if step_enabled(curr_step, args):
        export_csvs(collect_config_entries("experiment1", protocols, run_list), args)
    curr_step += 1

    if step_enabled(curr_step, args):
        export_csvs(collect_config_entries("experiment2", protocols, run_list), args)
    curr_step += 1

    if step_enabled(curr_step, args):
        extract_csvs(all_entries, args)
    curr_step += 1

    if step_enabled(curr_step, args):
        plot_protocol_legends()
        plot_cumulative("plotGoodputCumulativeDistribution.py")
    curr_step += 1

    if step_enabled(curr_step, args):
        plot_cumulative("plotRttCumulativeDistribution.py")
    curr_step += 1

    if step_enabled(curr_step, args):
        plot_cumulative("plotRetransmissionsCumulativeDistribution.py")
    curr_step += 1

    if step_enabled(curr_step, args):
        prepare_plot_dirs(all_entries)
    curr_step += 1

    if step_enabled(curr_step, args):
        plot_individual_runs(all_entries, args)

    print("\nExperiment 1 and 2 pipeline completed with all expected outputs present.\n")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"\nERROR: {exc}\n", file=sys.stderr)
        raise SystemExit(1)
