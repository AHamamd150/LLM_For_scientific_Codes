#!/usr/bin/env bash
set -euo pipefail

# Run tracer + critique only, using an already-generated analysis.
# The original frozen critique directory is not modified.
#
# Usage:
#   bash scripts/run_qwen3_32b_postreview.sh CASE RUN
#
# Examples:
#   bash scripts/run_qwen3_32b_postreview.sh 2 7
#   bash scripts/run_qwen3_32b_postreview.sh 5 1

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

MODEL="${MODEL:-Qwen/Qwen3-32B}"
PYTHON="${PYTHON:-python}"
N_RUNS="${N_RUNS:-1}"

PACKAGE_PATHS=(
  "$ROOT/packages/workbench-contracts/src"
  "$ROOT/packages/helper-selector/src"
  "$ROOT/packages/golden-axe-oracle/src"
  "$ROOT/packages/critique-pipeline/src"
  "$ROOT/backends/code-generator/src"
  "$ROOT/domains/lhco-domain/src"
  "$ROOT/workflows/src"
)

PACKAGE_PYTHONPATH="$(IFS=:; echo "${PACKAGE_PATHS[*]}")"
export PYTHONPATH="$PACKAGE_PYTHONPATH${PYTHONPATH:+:$PYTHONPATH}"

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 CASE RUN"
  echo "Example: $0 2 7"
  exit 2
fi

CASE="$1"
RUN="$2"

printf -v RUN_TAG "run_%02d" "$RUN"

CARD="$ROOT/examples/cases/user_input_6.txt"
CODE="$ROOT/frozen_timing/${RUN_TAG}/case${CASE}/execution/generated_analysis.py"
DOMAIN_CONTEXT="$ROOT/domains/lhco-domain/src/lhco_domain/prompts/critique_context.txt"

OUT="$ROOT/frozen_timing/${RUN_TAG}/case${CASE}/critique_qwen3_32b_case6card"

if [[ ! -f "$CARD" ]]; then
  echo "Error: card not found: $CARD" >&2
  exit 1
fi

if [[ ! -f "$CODE" ]]; then
  echo "Error: generated code not found: $CODE" >&2
  exit 1
fi

if [[ ! -f "$DOMAIN_CONTEXT" ]]; then
  echo "Error: critique context not found: $DOMAIN_CONTEXT" >&2
  exit 1
fi

if [[ -e "$OUT" ]]; then
  echo "Error: output directory already exists:" >&2
  echo "  $OUT" >&2
  echo "Refusing to overwrite it." >&2
  exit 1
fi

echo "Case:            $CASE"
echo "Run:             $RUN"
echo "Model:           $MODEL"
echo "Card:            $CARD"
echo "Generated code:  $CODE"
echo "Domain context:  $DOMAIN_CONTEXT"
echo "Output:          $OUT"
echo

ARGS=(
  "$PYTHON" -m critique_pipeline.cli run
  --card "$CARD"
  --code "$CODE"
  --tracer-model "$MODEL"
  --critique-model "$MODEL"
  --domain-context "$DOMAIN_CONTEXT"
  --n-runs "$N_RUNS"
  --no-repair
  --run-dir "$OUT"
)

if [[ -n "${MAX_ROUNDS:-}" ]]; then
  ARGS+=(--max-rounds "$MAX_ROUNDS")
fi
if [[ -n "${TRACER_MAX_TOKENS:-}" ]]; then
  ARGS+=(--tracer-max-tokens "$TRACER_MAX_TOKENS")
fi
if [[ -n "${CRITIQUE_MAX_TOKENS:-}" ]]; then
  ARGS+=(--critique-max-tokens "$CRITIQUE_MAX_TOKENS")
fi

"${ARGS[@]}"

echo
echo "Completed:"
echo "  $OUT"
