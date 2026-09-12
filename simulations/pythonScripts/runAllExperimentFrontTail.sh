#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export EXPERIMENT_CORES="${EXPERIMENT_CORES:-30}"
export LEO_SIMULATION_CORES="${LEO_SIMULATION_CORES:-15}"

plots=0
if [[ "${1:-}" == --plots ]]; then
    plots=1
    shift
fi
if [[ "${1:-}" == --help || "${1:-}" == -h || $# == 0 ]]; then
    echo "Usage: bash runAllExperimentFrontTail.sh [--plots] all|1 3 4 ..."
    echo "PINT OrbCC, Cubic, BBRv3, LeoCC, SaTCP where supported; 1 includes 2."
    echo "EXPERIMENT_CORES defaults to 30; LEO_SIMULATION_CORES defaults to 15."
    exit 0
fi
if [[ "$1" == all ]]; then
    set -- 1 3 4 5 6 7 8 9 10 11 13
fi
seen=" "
for number in "$@"; do
    [[ "$number" == 2 ]] && number=1
    case "$number" in
        1|3|4|5|6|7|8|9|10|11|13) ;;
        *) echo "No PINT FrontTail suite for experiment $number" >&2; exit 2 ;;
    esac
    [[ "$seen" == *" $number "* ]] && continue
    seen+="$number "
    runner="runExperiment${number}FrontTail.py"
    [[ "$number" == 1 ]] && runner="runExperiment1and2FrontTail.py"
    case "$number" in
        1) first=6; last=10 ;;
        3) first=4; last=9 ;;
        4|5|6|7|11) first=4; last=7 ;;
        8) first=5; last=7 ;;
        9) first=4; last=6 ;;
        10) first=4; last=7 ;;
        13) first=5; last=5 ;;
    esac
    echo "Experiment ${number}FrontTail: ${EXPERIMENT_CORES} workers (LEO simulations: ${LEO_SIMULATION_CORES})"
    (
        cd "$script_dir/experiment${number}FrontTail"
        if [[ "$plots" == 1 ]]; then
            START_STEP="$first" END_STEP="$last" python3 "$runner"
        else
            python3 "$runner"
        fi
    )
done
