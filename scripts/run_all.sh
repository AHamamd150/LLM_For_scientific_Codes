#!/usr/bin/env bash
set -euo pipefail

run_root="${1:-run_cfour2}"

for case_id in 1 2 3 4 5 ; do
  echo
  echo "========================================"
  echo "Running case ${case_id}"
  echo "Output: ${run_root}/case${case_id}"
  echo "========================================"

  ./scripts/run_qwen3_14b.sh \
    "examples/cases/user_input_${case_id}.txt" \
    "data/signal_${case_id}.lhco" \
    "${run_root}/case${case_id}"
done

echo
echo "All cases finished: ${run_root}"
