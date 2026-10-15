#!/usr/bin/env bash
set -euo pipefail

OUT_DIR="tracer_evaluation"
mkdir -p "$OUT_DIR"

run_evaluation() {
    local case="$1"
    local run="$2"

    printf -v run_dir "run_%02d" "$run"
    printf -v run_tag "%02d" "$run"

    local out_file="${OUT_DIR}/case${case}_run${run_tag}.csv"

    # Do not repeat completed evaluations
    if [[ -s "$out_file" ]]; then
        echo "=== Case ${case}, Run ${run}: already exists, skipping ==="
        return
    fi

    echo "=== Case ${case}, Run ${run} ==="

    python scripts/evaluate_tracer.py \
        --case "$case" \
        --run "$run" \
        --task-card "examples/cases/user_input_${case}.txt" \
        --code "frozen_timing/${run_dir}/case${case}/execution/generated_analysis.py" \
        --trace "frozen_timing/${run_dir}/case${case}/critique/tracer/final_output.txt" \
        --out "$out_file"
}

for case in 1 2 3 4 5; do
    for run in {1..10}; do
        run_evaluation "$case" "$run"
    done
done

echo "=== Tracer evaluation complete ==="
    
