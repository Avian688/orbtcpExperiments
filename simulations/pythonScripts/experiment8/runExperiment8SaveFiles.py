#!/usr/bin/env python3

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from raynetExperimentSupport import build_opp_run_command

SCRIPT_DIR = Path(__file__).resolve().parent
PAPER_EXPERIMENT_DIR = (SCRIPT_DIR / "../../paperExperiments/experiment8").resolve()
RESULTS_DIR = PAPER_EXPERIMENT_DIR / "results"
INI_FILE = "experiment8_saveFiles.ini"
CONFIGS = ["IslSave", "BentPipeSave"]


def opp_run_command(config_name):
    return build_opp_run_command(config_name, INI_FILE, include_leo=True)


def main():
    ini_path = PAPER_EXPERIMENT_DIR / INI_FILE
    if not ini_path.exists():
        print(f"ERROR: Missing INI file: {ini_path}", file=sys.stderr)
        return 1

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print("Starting experiment 8 save-file runs in parallel:")
    processes = []
    log_handles = []

    try:
        for config_name in CONFIGS:
            log_path = RESULTS_DIR / f"{config_name}.log"
            log_file = log_path.open("w", encoding="utf-8")
            log_handles.append(log_file)

            print(f"  - {config_name} started; log: {log_path}")
            process = subprocess.Popen(
                opp_run_command(config_name),
                cwd=PAPER_EXPERIMENT_DIR,
                stdout=log_file,
                stderr=subprocess.STDOUT,
            )
            processes.append((config_name, process, log_path))

        failures = []
        for config_name, process, log_path in processes:
            return_code = process.wait()
            if return_code == 0:
                print(f"  - {config_name} complete.")
            else:
                print(f"  - {config_name} failed with exit code {return_code}. See {log_path}")
                failures.append(config_name)

        if failures:
            print("Save-file runs finished with failures: " + ", ".join(failures))
            return 1

        print("Both save-file runs completed successfully.")
        return 0
    except KeyboardInterrupt:
        print("\nInterrupted; terminating save-file runs...")
        for _, process, _ in processes:
            if process.poll() is None:
                process.terminate()
        return 130
    finally:
        for log_file in log_handles:
            log_file.close()


if __name__ == "__main__":
    sys.exit(main())
