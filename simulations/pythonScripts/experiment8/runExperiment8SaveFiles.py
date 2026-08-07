#!/usr/bin/env python3

import subprocess
import sys
import time
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


def run_configs(config_names, capture_logs):
    active = []
    failures = []

    try:
        for config_name in config_names:
            command = opp_run_command(config_name)
            log_path = RESULTS_DIR / f"{config_name}.log" if capture_logs else None
            log_file = None
            output_kwargs = {
                "stdout": subprocess.DEVNULL,
                "stderr": subprocess.DEVNULL,
            }
            if log_path is not None:
                log_file = log_path.open("w", encoding="utf-8")
                log_file.write("$ " + " ".join(command) + "\n\n")
                log_file.flush()
                output_kwargs = {
                    "stdout": log_file,
                    "stderr": subprocess.STDOUT,
                }

            try:
                process = subprocess.Popen(
                    command,
                    cwd=PAPER_EXPERIMENT_DIR,
                    **output_kwargs,
                )
            except BaseException:
                if log_file is not None:
                    log_file.close()
                raise
            active.append((config_name, process, log_file, log_path))
            if log_path is None:
                print(f"  - {config_name} started; output suppressed")
            else:
                print(f"  - {config_name} retry started; log: {log_path}")

        while active:
            completed = [entry for entry in active if entry[1].poll() is not None]
            if not completed:
                time.sleep(0.1)
                continue

            for config_name, process, log_file, log_path in completed:
                active.remove((config_name, process, log_file, log_path))
                return_code = process.returncode
                if log_file is not None:
                    log_file.write(f"\nExit code: {return_code}\n")
                    log_file.close()

                if return_code == 0:
                    print(f"  - {config_name} complete.")
                else:
                    failures.append(config_name)
                    if log_path is None:
                        print(
                            f"  - {config_name} failed with exit code {return_code}; "
                            "retry output will be logged."
                        )
                    else:
                        print(
                            f"  - {config_name} failed with exit code {return_code}. "
                            f"See {log_path}"
                        )
    except BaseException:
        for _, process, log_file, _ in active:
            if process.poll() is None:
                process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            if log_file is not None and not log_file.closed:
                log_file.close()
        raise

    return failures


def main():
    ini_path = PAPER_EXPERIMENT_DIR / INI_FILE
    if not ini_path.exists():
        print(f"ERROR: Missing INI file: {ini_path}", file=sys.stderr)
        return 1

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    try:
        for config_name in CONFIGS:
            (RESULTS_DIR / f"{config_name}.log").unlink(missing_ok=True)

        print("Starting experiment 8 save-file runs in parallel:")
        failures = run_configs(CONFIGS, capture_logs=False)

        if failures:
            print("Retrying failed save-file runs with logging enabled:")
            failures = run_configs(failures, capture_logs=True)

        if failures:
            print("Save-file runs finished with failures: " + ", ".join(failures))
            return 1

        print("Both save-file runs completed successfully.")
        return 0
    except KeyboardInterrupt:
        print("\nInterrupted; terminating save-file runs...")
        return 130


if __name__ == "__main__":
    sys.exit(main())
