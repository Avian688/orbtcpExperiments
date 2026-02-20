#!/usr/bin/env python3

# Master runner for experiments 1 + 2 (only ones using Satcp + Leocc).
# - Generates scenarios + INIs
# - Runs opp_run configs in batches (cores) with progress prints (but opp_run output muted)
# - Exports vec->csv with progress prints (scavetool muted)
# - Extracts per-run csvs with progress prints (extract scripts muted)
# - Plots + merges PDFs with progress prints (plot scripts muted)
#
# Satcp + Leocc linking is included in opp_run via -n and -l (no -x excludes).

import subprocess
import time
from pathlib import Path


# ---------------- helpers ----------------

def run(cmd: str, *, cwd: Path | None = None, timeout: int | None = None,
        quiet: bool = False) -> None:
    """Run a single command and wait."""
    p = subprocess.Popen(
        cmd,
        shell=True,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.DEVNULL if quiet else None,
        stderr=subprocess.DEVNULL if quiet else None,
    )
    if timeout is None:
        p.wait()
    else:
        p.communicate(timeout=timeout)


def safe_rm(path: Path) -> None:
    if path.exists():
        run(f'rm -rf "{path}"', quiet=True)


def iter_config_names(ini_path: Path) -> list[str]:
    """Extract config names from lines like: [Config Foo]"""
    names = []
    for line in ini_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("[Config "):
            names.append(line[len("[Config "):-1])
    return names


def run_jobs_batched(
    jobs: list[tuple[str, Path, str]],
    *,
    cores: int,
    timeout: int | None = None,
    quiet: bool = True,
) -> None:
    """
    jobs: list of (cmd, cwd, label)
    Prints label on start and completion, but mutes subprocess output if quiet=True.
    """
    procs: list[tuple[subprocess.Popen, str]] = []
    started = 0
    completed = 0

    def start_job(cmd: str, cwd: Path, label: str) -> None:
        nonlocal started
        started += 1
        print(f"[START {started}] {label}")
        p = subprocess.Popen(
            cmd,
            shell=True,
            cwd=str(cwd),
            stdout=subprocess.DEVNULL if quiet else None,
            stderr=subprocess.DEVNULL if quiet else None,
        )
        procs.append((p, label))

    def drain() -> None:
        nonlocal completed
        for p, label in procs:
            p.wait(timeout=timeout)
            completed += 1
            print(f"[DONE  {completed}] {label}")
        procs.clear()

    for cmd, cwd, label in jobs:
        start_job(cmd, cwd, label)
        if len(procs) >= cores:
            drain()

    if procs:
        drain()


# ---------------- opp_run command (includes satcp + leocc) ----------------

OPP_N_PATH = (
    "../..:../../../src:"
    "../../../../bbr/simulations:../../../../bbr/src:"
    "../../../../inet4.5/examples:../../../../inet4.5/showcases:../../../../inet4.5/src:"
    "../../../../inet4.5/tests/validation:../../../../inet4.5/tests/networks:../../../../inet4.5/tutorials:"
    "../../../../tcpGoodputApplications/simulations:../../../../tcpGoodputApplications/src:"
    "../../../../tcpPaced/src:../../../../tcpPaced/simulations:"
    "../../../../cubic/simulations:../../../../cubic/src:"
    "../../../../leocc/simulations:../../../../leocc/src:"
    "../../../../leosatellites/src:../../../../leosatellites/simulations:"
    "../../../../os3/simulations:../../../../os3/src:"
    "../../../../orbtcp/simulations:../../../../orbtcp/src:"
    "../../../../satcp/simulations:../../../../satcp/src"
)

OPP_IMAGE_PATH = "../../../../inet4.5/images:../../../../os3/images"

OPP_LIBS = (
    "-l ../../../src/orbtcpExperiments "
    "-l ../../../../bbr/src/bbr "
    "-l ../../../../inet4.5/src/INET "
    "-l ../../../../tcpGoodputApplications/src/tcpGoodputApplications "
    "-l ../../../../tcpPaced/src/tcpPaced "
    "-l ../../../../cubic/src/cubic "
    "-l ../../../../leocc/src/leocc "
    "-l ../../../../leosatellites/src/leosatellites "
    "-l ../../../../os3/src/os3 "
    "-l ../../../../orbtcp/src/orbtcp "
    "-l ../../../../satcp/src/satcp"
)


def opp_run_cmd(config: str, ini_filename: str) -> str:
    return (
        "opp_run -r 0 -m -u Cmdenv "
        f"-c {config} "
        f"-n {OPP_N_PATH} "
        f"--image-path={OPP_IMAGE_PATH} "
        f"{OPP_LIBS} "
        f"{ini_filename}"
    )


# ---------------- main ----------------

def main() -> None:
    startStep = 1
    endStep = 9
    currStep = 1
    cores = 5

    experiments = ["experiment1", "experiment2"]
    runs = 50
    runList = list(range(1, runs + 1))

    # Only experiments 1 and 2 use satcp + leocc
    congControlList = ["bbr3", "bbr", "orbtcp", "cubic", "satcp", "leocc"]

    root = Path(__file__).resolve().parent
    paper = (root / "../../paperExperiments").resolve()
    plots = (root / "../../plots").resolve()

    exp1_dir = paper / "experiment1"
    exp2_dir = paper / "experiment2"

    # -------- STEP 1: generate + run experiment1 --------
    if currStep <= endStep and currStep >= startStep and "experiment1" in experiments:
        print("\n[STEP 1] Generating scenarios + INIs for experiment 1 + 2\n")
        run("python3 generateExperiment1Scenarios.py", cwd=root, timeout=300)
        run("python3 generateExperiment1IniFile.py", cwd=root, timeout=300)
        run("python3 ../experiment2/generateExperiment2Scenarios.py", cwd=root, timeout=300)
        run("python3 ../experiment2/generateExperiment2IniFile.py", cwd=root, timeout=300)

        safe_rm(root / "experiment1runTimes.txt")
        safe_rm(root / "experiment2runTimes.txt")

        for cc in congControlList:
            safe_rm(exp1_dir / "csvs" / cc)
            safe_rm(exp2_dir / "csvs" / cc)

        print("\n[STEP 1] Running Experiment 1 simulations (opp_run muted)\n")
        runtime_path = root / "experiment1runTimes.txt"
        runtime_path.write_text("--Experiment 1 Runtimes (s)--\n", encoding="utf-8")

        exp1_run_num = 1
        for cc in congControlList:
            ini_name = f"experiment1_{cc}.ini"
            ini_path = exp1_dir / ini_name
            if not ini_path.exists():
                print(f"[WARN] Missing ini: {ini_path}")
                continue

            config_names = iter_config_names(ini_path)
            jobs: list[tuple[str, Path, str]] = []
            for cfg in config_names:
                jobs.append((
                    opp_run_cmd(cfg, ini_name),
                    exp1_dir,
                    f"experiment1 / {cc} / {cfg}",
                ))

            # Run with our own progress; measure coarse batch time like your old script
            i = 0
            while i < len(jobs):
                batch = jobs[i:i + cores]
                t0 = time.time()
                run_jobs_batched(batch, cores=cores, quiet=True)
                dt = time.time() - t0
                with runtime_path.open("a", encoding="utf-8") as f:
                    for _ in batch:
                        f.write(f"Run {exp1_run_num}: {dt}\n")
                        exp1_run_num += 1
                i += cores

        time.sleep(2)

    currStep += 1

    # -------- STEP 2: run experiment2 --------
    if currStep <= endStep and currStep >= startStep and "experiment2" in experiments:
        print("\n[STEP 2] Running Experiment 2 simulations (opp_run muted)\n")
        runtime_path = root / "experiment2runTimes.txt"
        runtime_path.write_text("--Experiment 2 Runtimes (s)--\n", encoding="utf-8")

        exp2_run_num = 1
        for cc in congControlList:
            ini_name = f"experiment2_{cc}.ini"
            ini_path = exp2_dir / ini_name
            if not ini_path.exists():
                print(f"[WARN] Missing ini: {ini_path}")
                continue

            config_names = iter_config_names(ini_path)
            jobs: list[tuple[str, Path, str]] = []
            for cfg in config_names:
                jobs.append((
                    opp_run_cmd(cfg, ini_name),
                    exp2_dir,
                    f"experiment2 / {cc} / {cfg}",
                ))

            i = 0
            while i < len(jobs):
                batch = jobs[i:i + cores]
                t0 = time.time()
                run_jobs_batched(batch, cores=cores, quiet=True)
                dt = time.time() - t0
                with runtime_path.open("a", encoding="utf-8") as f:
                    for _ in batch:
                        f.write(f"Run {exp2_run_num}: {dt}\n")
                        exp2_run_num += 1
                i += cores

        time.sleep(2)

    currStep += 1

    # -------- STEP 3: export vec->csv (experiment1) --------
    if currStep <= endStep and currStep >= startStep:
        print("\n[STEP 3] Exporting .vec -> .csv for experiment 1 (scavetool muted)\n")
        vec_dir = exp1_dir / "results"
        jobs: list[tuple[str, Path, str]] = []
        for vec in sorted(vec_dir.glob("*.vec")):
            cmd = f'opp_scavetool export -o "results/{vec.stem}.csv" -F CSV-R "results/{vec.name}"'
            jobs.append((cmd, exp1_dir, f"exp1 export {vec.name} -> {vec.stem}.csv"))
        run_jobs_batched(jobs, cores=cores, quiet=True)
        time.sleep(1)

    currStep += 1

    # -------- STEP 4: export vec->csv (experiment2) --------
    if currStep <= endStep and currStep >= startStep:
        print("\n[STEP 4] Exporting .vec -> .csv for experiment 2 (scavetool muted)\n")
        vec_dir = exp2_dir / "results"
        jobs = []
        for vec in sorted(vec_dir.glob("*.vec")):
            cmd = f'opp_scavetool export -o "results/{vec.stem}.csv" -F CSV-R "results/{vec.name}"'
            jobs.append((cmd, exp2_dir, f"exp2 export {vec.name} -> {vec.stem}.csv"))
        run_jobs_batched(jobs, cores=cores, quiet=True)
        time.sleep(1)

    currStep += 1

    # -------- STEP 5: extract CSV data --------
    if currStep <= endStep and currStep >= startStep:
        print("\n[STEP 5] Extracting CSV data (extract scripts muted)\n")
        jobs = []
        for exp in experiments:
            runNam = "Run" if exp == "experiment1" else "LossRun"
            for protocol in congControlList:
                for run_num in runList:
                    csv_path = paper / exp / "results" / f"{protocol.title()}_{runNam}{run_num}.csv"
                    if csv_path.exists():
                        cmd = f'python3 extractSingleCsvFile.py "{csv_path}" {exp} {protocol} {run_num}'
                        jobs.append((cmd, root, f"extract {exp}/{protocol} run{run_num}"))
        run_jobs_batched(jobs, cores=cores, timeout=300, quiet=True)
        time.sleep(1)

    currStep += 1

    # -------- STEP 6: plot goodput CDF --------
    if currStep <= endStep and currStep >= startStep:
        print("\n[STEP 6] Plotting goodput CDF (muted)\n")
        out_cdf = plots / "experiment1and2Cumulative"
        out_cdf.mkdir(parents=True, exist_ok=True)
        run("python3 ../../pythonScripts/experiment1/plotGoodputCumulativeDistribution.py",
            cwd=out_cdf, timeout=3600, quiet=True)

    currStep += 1

    # -------- STEP 7: plot RTT CDF --------
    if currStep <= endStep and currStep >= startStep:
        print("\n[STEP 7] Plotting RTT CDF (muted)\n")
        out_cdf = plots / "experiment1and2Cumulative"
        out_cdf.mkdir(parents=True, exist_ok=True)
        run("python3 ../../pythonScripts/experiment1/plotRttCumulativeDistribution.py",
            cwd=out_cdf, timeout=3600, quiet=True)

    currStep += 1

    # -------- STEP 8: make plot directories --------
    if currStep <= endStep and currStep >= startStep:
        print("\n[STEP 8] Creating plot directories\n")
        for exp in experiments:
            exp_plot_dir = plots / exp
            exp_plot_dir.mkdir(parents=True, exist_ok=True)
            for cc in congControlList:
                cc_dir = exp_plot_dir / cc
                cc_dir.mkdir(parents=True, exist_ok=True)
                for run_num in runList:
                    (cc_dir / f"run{run_num}").mkdir(parents=True, exist_ok=True)
        time.sleep(1)

    currStep += 1

    # -------- STEP 9: plot per-run + merge pdfs --------
    if currStep <= endStep and currStep >= startStep:
        print("\n[STEP 9] Plotting per-run figures + merging PDFs (muted)\n")
        plot_jobs: list[tuple[str, Path, str]] = []
        merge_jobs: list[tuple[str, Path, str]] = []

        for exp in experiments:
            for protocol in congControlList:
                for run_num in runList:
                    base = paper / exp / "csvs" / protocol / f"run{run_num}"
                    goodput = base / "singledumbbell.server[0].app[0]" / "goodput.csv"
                    throughput = base / "singledumbbell.server[0].tcp.conn" / "throughput.csv"
                    cwnd = base / "singledumbbell.client[0].tcp.conn" / "cwnd.csv"
                    queue = base / "singledumbbell.router1.ppp[1].queue" / "queueLength.csv"
                    rtt = base / "singledumbbell.client[0].tcp.conn" / "rtt.csv"
                    inflight = base / "singledumbbell.client[0].tcp.conn" / "mbytesInFlight.csv"

                    if not (goodput.exists() or throughput.exists() or cwnd.exists() or queue.exists()):
                        continue

                    out_dir = plots / exp / protocol / f"run{run_num}"
                    out_dir.mkdir(parents=True, exist_ok=True)

                    plot_jobs.extend([
                        (f'python3 ../../../../pythonScripts/experiment1/plotGoodput.py "../../{goodput}"', out_dir,
                         f"plot goodput {exp}/{protocol} run{run_num}"),
                        (f'python3 ../../../../pythonScripts/experiment1/plotThroughput.py "../../{throughput}"', out_dir,
                         f"plot throughput {exp}/{protocol} run{run_num}"),
                        (f'python3 ../../../../pythonScripts/experiment1/plotCwnd.py "../../{cwnd}"', out_dir,
                         f"plot cwnd {exp}/{protocol} run{run_num}"),
                        (f'python3 ../../../../pythonScripts/experiment1/plotQueueLength.py "../../{queue}"', out_dir,
                         f"plot queue {exp}/{protocol} run{run_num}"),
                        (f'python3 ../../../../pythonScripts/experiment1/plotRtt.py "../../{rtt}"', out_dir,
                         f"plot rtt {exp}/{protocol} run{run_num}"),
                        (f'python3 ../../../../pythonScripts/experiment1/plotBytesInFlight.py "../../{inflight}"', out_dir,
                         f"plot inflight {exp}/{protocol} run{run_num}"),
                    ])
                    merge_jobs.append((
                        "python3 ../../../../pythonScripts/experiment1/mergePdfs.py",
                        out_dir,
                        f"merge pdfs {exp}/{protocol} run{run_num}",
                    ))

        run_jobs_batched(plot_jobs, cores=cores, timeout=300, quiet=True)
        run_jobs_batched(merge_jobs, cores=cores, timeout=300, quiet=True)


if __name__ == "__main__":
    main()