#!/usr/bin/env bash

for CASE in {1..5}; do
  for RUN in {1..10}; do
    printf -v RUN_TAG "run_%02d" "$RUN"
    OUT="frozen_timing/${RUN_TAG}/case${CASE}/critique_qwen3_32b"

    if [[ -e "$OUT" ]]; then
      echo "[SKIP] case${CASE} run${RUN}: already exists"
      continue
    fi

    echo "========================================"
    echo "[RUN] case${CASE} run${RUN}"
    echo "========================================"

    if ! bash scripts/run_qwen3_32b_postreview.sh "$CASE" "$RUN"; then
      echo "[FAILED] case${CASE} run${RUN}" >&2
    fi
  done
done
