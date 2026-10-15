#!/usr/bin/env bash
set -euo pipefail

OUT_DIR="tracer_evaluation_32b"

git_commit=$(git rev-parse HEAD)
git_status=$(git status --short)


mkdir -p "$OUT_DIR"

printf '%s\n' "$git_commit" > "${OUT_DIR}/git_commit.txt"
printf '%s\n' "$git_status" > "${OUT_DIR}/git_status.txt"

cp "$0" "${OUT_DIR}/"


run_evaluation() {
    local case="$1"
    local run="$2"

    printf -v run_dir "run_%02d" "$run"
    printf -v run_tag "%02d" "$run"

    local out_file="${OUT_DIR}/case${case}_run${run_tag}.csv"
    local case_dir="case${case}_32b_end2end/${run_dir}/case${case}"

    # Do not repeat completed evaluations
    if [[ -s "$out_file" ]]; then
        echo "=== Case ${case}, Run ${run}: already exists, skipping ==="
        return
    fi

    echo "=== Case ${case}, Run ${run} ==="

    python evaluate_tracer.py \
        --case "$case" \
        --run "$run" \
        --task-card "examples/cases/user_input_${case}.txt" \
        --code "${case_dir}/execution/generated_analysis.py" \
        --trace "${case_dir}/critique/tracer/final_output.txt" \
        --out "$out_file"
}

for case in 2 6; do
    for run in {1..10}; do
        run_evaluation "$case" "$run"
    done
done

echo "=== Tracer evaluation complete ==="
    
