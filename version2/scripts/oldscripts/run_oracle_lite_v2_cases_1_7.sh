#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

OUT_ROOT="${OUT_ROOT:-$ROOT/oracle_lite_v2_14b_10runs}"

mkdir -p "$OUT_ROOT"

for CASE in {1..7}; do
    CARD="$ROOT/examples/cases/user_input_${CASE}.txt"
    RUN_DIR="$OUT_ROOT/case${CASE}"

    echo
    echo "========================================"
    echo "Oracle-lite-v2: Case ${CASE}"
    echo "Card:    $CARD"
    echo "Output:  $RUN_DIR"
    echo "========================================"

    RUNS=10 \
      "$ROOT/scripts/run_oracle_lite_v2.sh" \
      "$CARD" \
      "$RUN_DIR"
done

echo
echo "Completed all Oracle-lite-v2 runs."
echo "Results: $OUT_ROOT"
