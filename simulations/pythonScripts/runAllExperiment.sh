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
  ./runAllExperiment.sh --plots all
  ./runAllExperiment.sh --plots 1 3 8
  EXPERIMENT_CORES=30 ./runAllExperiment.sh all
  EXPERIMENT_CORES=30 LEO_SIMULATION_CORES=20 ./runAllExperiment.sh 8 9 10

Notes:
  experiment2 is covered by experiment1/runExperiment1and2.py.
  --plots runs only the plot-directory, plotting, and PDF-merge steps using existing extracted data.
  --plots all also includes experimentAvgRTT, experimentInitNumFlows, experimentTuning,
  and experimentTuningDynamic.
  LEO_SIMULATION_CORES controls only Experiment 8-10 simulation workers and defaults to 15.
  EXPERIMENT_CORES still controls their CSV export, extraction, and plotting workers.
  Experiment 3+ simulation attempts time out after 9000 seconds and retry three times by default.
  Override with EXPERIMENT_SIM_TIMEOUT_SECONDS, EXPERIMENT_RETRIES, or EXPERIMENT_RESUME=1.
  If no arguments are supplied, the script falls back to the interactive menu.
EOF
}

plot_steps_for_experiment() {
  case "$1" in
    0) echo "5 5 experiment" ;;
    1) echo "6 10 standard" ;;
    3) echo "4 9 standard" ;;
    4|5|6|7) echo "4 7 standard" ;;
    8) echo "5 7 standard" ;;
    9) echo "4 6 standard" ;;
    10) echo "4 7 standard" ;;
    11) echo "4 7 standard" ;;
    12|13) echo "5 5 standard" ;;
    *) return 1 ;;
  esac
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
  local start_step=""
  local end_step=""
  local step_env=""

  if [[ "$i" == "1" ]]; then
    script="runExperiment1and2.py"
  fi

  echo "==============================="
  echo "Running $script in $folder"
  echo "Working directory: $script_dir/$folder"
  if [[ "$plot_only" -eq 1 ]]; then
    read -r start_step end_step step_env < <(plot_steps_for_experiment "$i")
    echo "Plot-only steps: $start_step-$end_step"
  fi
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
    if [[ "$plot_only" -eq 0 ]]; then
      python3 "$script"
    elif [[ "$step_env" == "experiment" ]]; then
      EXPERIMENT_START_STEP="$start_step" EXPERIMENT_END_STEP="$end_step" python3 "$script"
    else
      START_STEP="$start_step" END_STEP="$end_step" python3 "$script"
    fi
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

run_named_plot_experiment() {
  local folder="$1"
  local script="$2"
  local start_step="$3"
  local end_step="$4"

  echo "==============================="
  echo "Plotting $folder with $script"
  echo "Working directory: $script_dir/$folder"
  echo "Plot-only steps: $start_step-$end_step"

  if [[ ! -f "$script_dir/$folder/$script" ]]; then
    echo "Missing experiment script: $script_dir/$folder/$script" >&2
    return 1
  fi

  (
    cd "$script_dir/$folder" || exit 1
    START_STEP="$start_step" END_STEP="$end_step" python3 "$script"
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

plot_only=0
if [[ "${1:-}" == "--plots" ]]; then
  plot_only=1
  shift
fi

experiments=()
all_selected=0
if [[ "$#" -eq 0 ]]; then
  if [[ "$plot_only" -eq 1 ]]; then
    echo "--plots requires 'all' or one or more experiment numbers." >&2
    usage
    exit 1
  else
    while IFS= read -r exp; do
      experiments+=("$exp")
    done < <(collect_interactive_selection)
  fi
elif [[ "$1" == "-h" || "$1" == "--help" ]]; then
  usage
  exit 0
elif [[ "$1" == "all" ]]; then
  experiments=("${default_experiments[@]}")
  all_selected=1
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

if [[ "$plot_only" -eq 1 && "$all_selected" -eq 1 ]]; then
  if ! run_named_plot_experiment "experimentAvgRTT" "runExperimentAvgRTT.py" 4 7; then
    failures+=("experimentAvgRTT")
  fi
  if ! run_named_plot_experiment "experimentInitNumFlows" "runExperimentInitNumFlows.py" 4 8; then
    failures+=("experimentInitNumFlows")
  fi
  if ! run_named_plot_experiment "experimentTuning" "runExperimentTuning.py" 5 5; then
    failures+=("experimentTuning")
  fi
  if ! run_named_plot_experiment "experimentTuningDynamic" "runExperimentTuningDynamic.py" 5 5; then
    failures+=("experimentTuningDynamic")
  fi
fi

if [[ "${#failures[@]}" -gt 0 ]]; then
  echo "The following experiment runner(s) failed: ${failures[*]}" >&2
  exit 1
fi

echo "All selected experiments completed successfully."
