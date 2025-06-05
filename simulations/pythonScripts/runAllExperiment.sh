#!/bin/bash

# Save the absolute path to the script's root directory
root_dir="$(pwd)"

run_experiment() {
  local i=$1
  local folder="experiment$i"
  local script

  if [ "$i" -eq 1 ]; then
    script="runExperiment1and2.py"
  else
    script="runExperiment$i.py"
  fi

  echo "==============================="
  echo "Running $script in $folder..."

  (
    cd "$root_dir/$folder" || { echo "Failed to cd into $folder"; exit 1; }
    echo "Current working directory: $(pwd)"
    echo "Executing: python3 $script"
    python3 "$script"
  )

  echo "Finished $script in $folder."
  echo "==============================="
}

echo "Choose an option:"
echo "1) Run all experiments (excluding experiment2)"
echo "2) Run specific experiments (e.g. 1 3 5)"
read -rp "Enter 1 or 2: " choice

if [ "$choice" == "1" ]; then
  for i in {1..6}; do
    if [ "$i" -eq 2 ]; then
      continue
    fi
    run_experiment "$i"
  done
  echo "All experiments completed."

elif [ "$choice" == "2" ]; then
  read -rp "Enter experiment numbers separated by space (e.g. 1 3 5): " -a selected
  seen=()

  include_exp1=false

  for num in "${selected[@]}"; do
    if ! [[ "$num" =~ ^[1-6]$ ]]; then
      echo "Invalid experiment number: $num"
      continue
    fi
    if [ "$num" -eq 2 ]; then
      echo "Skipping experiment2 — it is covered by experiment1."
      continue
    fi
    if [ "$num" -eq 1 ]; then
      include_exp1=true
    fi
    # Avoid duplicates
    if [[ ! " ${seen[*]} " =~ " $num " ]]; then
      seen+=("$num")
    fi
  done

  # If 1 is in the list, skip 2 if present
  if [ "$include_exp1" = true ]; then
    seen=( "${seen[@]/2}" )  # Remove 2 if it’s there
  fi

  for exp in "${seen[@]}"; do
    run_experiment "$exp"
  done

  echo "Selected experiments completed."
else
  echo "Invalid choice."
  exit 1
fi