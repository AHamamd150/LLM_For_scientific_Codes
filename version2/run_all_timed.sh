#!/usr/bin/env bash
set -euo pipefail

run_root="${1:-timing_run}"
n_runs="${2:-1}"

# Preserve previous runs: never reuse an existing output directory.
if [[ -e "${run_root}" ]]; then
  echo "Error: output directory already exists: ${run_root}" >&2
  echo "Choose a new run_root to avoid overwriting run data." >&2
  exit 1
fi

mkdir -p "${run_root}"

timing_file="${run_root}/timing_cases1_7.tsv"
printf "run\tcase\tstart_time\tend_time\tseconds\tstatus\n" > "${timing_file}"

for run_id in $(seq 1 "${n_runs}"); do
  run_dir="${run_root}/run_$(printf '%02d' "${run_id}")"
  mkdir -p "${run_dir}"

  echo
  echo "########################################"
  echo "Run ${run_id} / ${n_runs}"
  echo "########################################"

  for case_id in 1 2 3 4 5 6 7; do
    case_dir="${run_dir}/case${case_id}"

    # Cases 6 and 7 revise the task cards for Cases 2 and 5.
    signal_case="${case_id}"
    case "${case_id}" in
      6) signal_case=2 ;;
      7) signal_case=5 ;;
    esac

    echo
    echo "========================================"
    echo "Running case ${case_id}"
    echo "Output: ${case_dir}"
    echo "========================================"

    # Portable on both macOS (BSD date) and Linux (GNU date).
    start_time=$(date '+%Y-%m-%dT%H:%M:%S%z')
    start_sec=$(python3 -c 'import time; print(time.time())')

    if ./scripts/run_qwen3_14b.sh \
       "examples/cases/user_input_${case_id}.txt" \
       "data/signal_${signal_case}.lhco" \
       "${case_dir}"
    then
      status="success"
    else
      status="failed"
    fi

    end_sec=$(python3 -c 'import time; print(time.time())')
    end_time=$(date '+%Y-%m-%dT%H:%M:%S%z')

    elapsed=$(awk -v start="${start_sec}" -v end="${end_sec}" \
      'BEGIN { printf "%.3f", end-start }')

    printf "%s\t%s\t%s\t%s\t%s\t%s\n" \
      "${run_id}" \
      "${case_id}" \
      "${start_time}" \
      "${end_time}" \
      "${elapsed}" \
      "${status}" \
      >> "${timing_file}"

    echo "Case ${case_id}: ${elapsed} s (${status})"
  done
done

echo
echo "All runs finished."
echo "Timing results: ${timing_file}"
