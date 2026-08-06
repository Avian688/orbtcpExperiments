#!/usr/bin/env bash

set -uo pipefail

export LEO_SIMULATION_CORES="${LEO_SIMULATION_CORES:-15}"

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
default_experiments=(0 1 3 4 5 6 7 8 9 10 11 12 13)

usage() {
  cat <<'EOF'
Usage:
  ./runAllExperiment.sh all
  ./runAllExperiment.sh 0 1 3 5 9
  EXPERIMENT_CORES=30 ./runAllExperiment.sh all
  EXPERIMENT_CORES=30 LEO_SIMULATION_CORES=20 ./runAllExperiment.sh 8 9 10

Notes:
  experiment2 is covered by experiment1/runExperiment1and2.py.
  LEO_SIMULATION_CORES controls only Experiment 8-10 simulation workers and defaults to 15.
  EXPERIMENT_CORES still controls their CSV export, extraction, and plotting workers.
  Experiment 3+ simulation attempts time out after 9000 seconds and retry three times by default.
  Override with EXPERIMENT_SIM_TIMEOUT_SECONDS, EXPERIMENT_RETRIES, or EXPERIMENT_RESUME=1.
  If no arguments are supplied, the script falls back to the interactive menu.
EOF
}

valid_experiment() {
  [[ "$1" =~ ^(0|1|2|3|4|5|6|7|8|9|10|11|12|13)$ ]]
}

dedupe_experiments() {
  local seen=" "
  local selected=()
  local num

  for num in "$@"; do
    if ! valid_experiment "$num"; then
      echo "Invalid experiment number: $num" >&2
      return 1
    fi
    if [[ "$num" == "2" ]]; then
      echo "Skipping experiment2 because it is covered by experiment1." >&2
      continue
    fi
    if [[ "$seen" != *" $num "* ]]; then
      selected+=("$num")
      seen+="$num "
    fi
  done

  if [[ "${#selected[@]}" -gt 0 ]]; then
    printf '%s\n' "${selected[@]}"
  fi
}

run_experiment() {
  local i="$1"
  local folder="experiment$i"
  local script="runExperiment$i.py"

  if [[ "$i" == "1" ]]; then
    script="runExperiment1and2.py"
  fi

  echo "==============================="
  echo "Running $script in $folder"
  echo "Working directory: $script_dir/$folder"
  if [[ -n "${EXPERIMENT_CORES:-}" ]]; then
    echo "EXPERIMENT_CORES=$EXPERIMENT_CORES"
  fi
  if [[ "$i" =~ ^(8|9|10)$ ]]; then
    echo "LEO_SIMULATION_CORES=$LEO_SIMULATION_CORES"
  fi

  if [[ ! -d "$script_dir/$folder" ]]; then
    echo "Missing experiment folder: $script_dir/$folder" >&2
    return 1
  fi
  if [[ ! -f "$script_dir/$folder/$script" ]]; then
    echo "Missing experiment script: $script_dir/$folder/$script" >&2
    return 1
  fi

  (
    cd "$script_dir/$folder" || exit 1
    python3 "$script"
  )
  local status=$?

  if [[ "$status" -eq 0 ]]; then
    echo "Finished $script successfully."
  else
    echo "FAILED $script with exit code $status." >&2
  fi
  echo "==============================="
  return "$status"
}

collect_interactive_selection() {
  local choice
  echo "Choose an option:" >&2
  echo "1) Run all experiments (experiment2 is included via experiment1)" >&2
  echo "2) Run specific experiments (e.g. 0 1 3 5)" >&2
  read -rp "Enter 1 or 2: " choice

  if [[ "$choice" == "1" ]]; then
    printf '%s\n' "${default_experiments[@]}"
  elif [[ "$choice" == "2" ]]; then
    local selected=()
    read -rp "Enter experiment numbers separated by space (e.g. 0 1 3 5): " -a selected
    dedupe_experiments "${selected[@]}"
  else
    echo "Invalid choice." >&2
    return 1
  fi
}

experiments=()
if [[ "$#" -eq 0 ]]; then
  while IFS= read -r exp; do
    experiments+=("$exp")
  done < <(collect_interactive_selection)
elif [[ "$1" == "-h" || "$1" == "--help" ]]; then
  usage
  exit 0
elif [[ "$1" == "all" ]]; then
  experiments=("${default_experiments[@]}")
else
  while IFS= read -r exp; do
    experiments+=("$exp")
  done < <(dedupe_experiments "$@")
fi

if [[ "${#experiments[@]}" -eq 0 ]]; then
  echo "No experiments selected." >&2
  exit 1
fi

failures=()
for exp in "${experiments[@]}"; do
  if ! run_experiment "$exp"; then
    failures+=("$exp")
  fi
done

if [[ "${#failures[@]}" -gt 0 ]]; then
  echo "The following experiment runner(s) failed: ${failures[*]}" >&2
  exit 1
fi

echo "All selected experiments completed successfully."
