#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

MODEL="${MODEL:-Qwen/Qwen3-32B}"
MAX_RETRIES="${MAX_RETRIES:-3}"
PYTHON="${PYTHON:-python}"
ORACLE_PROFILE="${ORACLE_PROFILE:-oracle}"
ORACLE_OUTPUT_CONTRACT="${ORACLE_OUTPUT_CONTRACT:-auto}"
ORACLE_MAX_TOKENS="${ORACLE_MAX_TOKENS:-1800}"
ORACLE_TEMPERATURE="${ORACLE_TEMPERATURE:-0.2}"

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

WORKBENCH=("$PYTHON" -m codegen_workflows.cli)
ORACLE=("$PYTHON" -m golden_axe.cli)

if [[ $# -ne 3 ]]; then
  echo "Usage: $0 CARD LHCO_FILE RUN_DIR"
  echo
  echo "Environment variables:"
  echo "  HF_TOKEN             Hugging Face access token (required)"
  echo "  MODEL                Model ID for every main workflow component"
  echo "                       default: Qwen/Qwen3-14B"
  echo "  MAX_RETRIES          Fix-then-regenerate trials"
  echo "                       default: 3"
  echo "  ORACLE_PROFILE       Post-run Oracle profile"
  echo "                       default: oracle"
  echo "  ORACLE_OUTPUT_CONTRACT  auto, system, domain, or none (default: auto)"
  echo "  ORACLE_MAX_TOKENS    Oracle max tokens"
  echo "                       default: 1800"
  echo "  ORACLE_TEMPERATURE   Oracle sampling temperature"
  echo "                       default: 0.2"
  exit 2
fi

CARD="$1"
LHCO_FILE="$2"
RUN_DIR="$3"

if [[ -z "${HF_TOKEN:-}" ]]; then
  echo "Error: HF_TOKEN is not set." >&2
  exit 1
fi

if [[ ! -f "$CARD" ]]; then
  echo "Error: card not found: $CARD" >&2
  exit 1
fi

if [[ ! -f "$LHCO_FILE" ]]; then
  echo "Error: LHCO file not found: $LHCO_FILE" >&2
  exit 1
fi

mkdir -p "$RUN_DIR/cards" "$RUN_DIR/oracle"
cp "$CARD" "$RUN_DIR/cards/original.txt"

ORACLE_CONTEXT=""
ORACLE_CONTEXT_ARGS=()
case "$ORACLE_PROFILE" in
  oracle|oracle-split-v3)
    ORACLE_CONTEXT="$ROOT/domains/lhco-domain/src/lhco_domain/prompts/oracle_context.txt"
    ;;
  oraclet)
    ORACLE_CONTEXT="$ROOT/domains/lhco-domain/src/lhco_domain/prompts/oraclet_domain_prompt.txt"
    ;;
esac
if [[ -n "$ORACLE_CONTEXT" ]]; then
  ORACLE_CONTEXT_ARGS=(--oracle-context "$ORACLE_CONTEXT")
fi

echo "Model:          $MODEL"
echo "Run directory:  $RUN_DIR"
echo "Oracle profile: $ORACLE_PROFILE"
echo "Oracle output:  $ORACLE_OUTPUT_CONTRACT"
echo
echo "[1/2] Helper selection, generation, execution recovery, and critique"

"${WORKBENCH[@]}" generate-review \
  --card "$CARD" \
  --domain-assets "lhco_domain:DOMAIN" \
  --helper-model "$MODEL" \
  --generator-model "$MODEL" \
  --fixer-model "$MODEL" \
  --tracer-model "$MODEL" \
  --critique-model "$MODEL" \
  --critique-runs 1 \
  --input "$LHCO_FILE" \
  --max-retries "$MAX_RETRIES" \
  --run-dir "$RUN_DIR"

echo
echo "[2/2] Post-run Oracle ambiguity review"

"${ORACLE[@]}" run \
  --card "$CARD" \
  --registry-module "lhco_domain.registry:HELPER_REGISTRY" \
  --profile "$ORACLE_PROFILE" \
  --oracle-output-contract "$ORACLE_OUTPUT_CONTRACT" \
  "${ORACLE_CONTEXT_ARGS[@]}" \
  --model "$MODEL" \
  --hf-token "$HF_TOKEN" \
  --max-tokens "$ORACLE_MAX_TOKENS" \
  --temperature "$ORACLE_TEMPERATURE" \
  --run-dir "$RUN_DIR/oracle"

echo
echo "Completed: $RUN_DIR"
echo "Oracle review: $RUN_DIR/oracle/response_001.txt"
