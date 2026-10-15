#!/usr/bin/env bash
set -euo pipefail

# Bundle tracer + critique outputs for frozen 14B runs.
#
# Usage:
#   bash make_tracer_critique_bundle.sh 1
#   bash make_tracer_critique_bundle.sh 5
#   bash make_tracer_critique_bundle.sh all
#
# Expected structure:
#   frozen_timing/run_01/case1/
#   ...
#   frozen_timing/run_10/case5/
#
# Run from the repository root.

make_bundle() {
    local case_id="$1"

    if [[ ! "$case_id" =~ ^[1-7]$ ]]; then
        echo "Error: case_id must be 1- 7." >&2
        return 1
    fi

    local out="case${case_id}_tracer_critique_bundle.zip"
    local tmpdir="case${case_id}_tracer_critique_bundle"

    echo "=== Building Case ${case_id} bundle ==="

    rm -rf "$tmpdir" "$out"
    mkdir -p "$tmpdir"

    local task_card="examples/cases/user_input_${case_id}.txt"
    if [[ -f "$task_card" ]]; then
        mkdir -p "$tmpdir/examples/cases"
        cp "$task_card" "$tmpdir/examples/cases/"
    elif [[ -f "user_input_${case_id}.txt" ]]; then
        cp "user_input_${case_id}.txt" "$tmpdir/"
    else
        echo "Warning: user_input_${case_id}.txt not found."
    fi

    local copied_runs=0

    for run in $(seq -w 1 10); do
        local src="frozen_timing/run_${run}/case${case_id}"
        local dst="${tmpdir}/frozen_timing/run_${run}/case${case_id}"

        if [[ ! -d "$src" ]]; then
            echo "Warning: $src not found; skipping."
            continue
        fi

        mkdir -p "$dst"

        if [[ -f "$src/execution/generated_analysis.py" ]]; then
            mkdir -p "$dst/execution"
            cp "$src/execution/generated_analysis.py" "$dst/execution/"
        else
            echo "Warning: $src/execution/generated_analysis.py not found."
        fi

        if [[ -f "$src/execution/cutflow.txt" ]]; then
            mkdir -p "$dst/execution"
            cp "$src/execution/cutflow.txt" "$dst/execution/"
        fi

        if [[ -d "$src/critique" ]]; then
            cp -R "$src/critique" "$dst/"
        else
            echo "Warning: $src/critique not found."
        fi

        copied_runs=$((copied_runs + 1))
    done

    {
        echo "Case ${case_id} tracer + critique bundle"
        echo
        echo "Source: frozen_timing"
        echo "Runs copied: ${copied_runs}/10"
        echo
        echo "Expected contents for each run:"
        echo "  execution/generated_analysis.py"
        echo "  execution/cutflow.txt              (if present)"
        echo "  critique/tracer/final_output.txt"
        echo "  critique/findings/filtered_review.txt"
        echo "  plus other files under critique/"
    } > "${tmpdir}/README.txt"

    zip -r "$out" "$tmpdir" >/dev/null
    rm -rf "$tmpdir"

    echo "Created: $out"
}

case "${1:-}" in
    1|2|3|4|5|6|7)
        make_bundle "$1"
        ;;
    all)
        for case_id in 6 7; do
            make_bundle "$case_id"
        done
        ;;
    *)
        echo "Usage: $0 {1|2|3|4|5|6|7|all}" >&2
        exit 1
        ;;
esac
