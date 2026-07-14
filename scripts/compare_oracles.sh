#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

MODEL="${MODEL:-Qwen/Qwen3-14B}"
RUNS="${RUNS:-3}"
MAX_TOKENS="${MAX_TOKENS:-1800}"
TEMPERATURE="${TEMPERATURE:-0.2}"
PYTHON="${PYTHON:-python}"
DOMAIN="${DOMAIN:-lhco}"
SPLIT_PROFILE="${SPLIT_PROFILE:-oracle}"
CANONICAL_PROFILE="${CANONICAL_PROFILE:-oracle-lite}"
ORACLE_OUTPUT_CONTRACT="${ORACLE_OUTPUT_CONTRACT:-auto}"

PACKAGE_PATHS=(
  "$ROOT/packages/helper-selector/src"
  "$ROOT/packages/golden-axe-oracle/src"
  "$ROOT/domains/${DOMAIN}-domain/src"
)

PACKAGE_PYTHONPATH="$(IFS=:; echo "${PACKAGE_PATHS[*]}")"
export PYTHONPATH="$PACKAGE_PYTHONPATH${PYTHONPATH:+:$PYTHONPATH}"

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 CARD RUN_DIR"
  echo
  echo "Runs the legacy monolithic oracle and release oracle the same number of times."
  echo
  echo "Environment variables:"
  echo "  HF_TOKEN      Hugging Face access token (required)"
  echo "  MODEL         Model ID (default: Qwen/Qwen3-14B)"
  echo "  DOMAIN        Domain name without '-domain' (default: lhco)"
  echo "  CANONICAL_PROFILE Legacy profile to compare (default: oracle-lite)"
  echo "  SPLIT_PROFILE Release/split profile to compare (default: oracle)"
  echo "  ORACLE_OUTPUT_CONTRACT  auto, system, domain, or none (default: auto)"
  echo "  RUNS          Number of runs for each profile (default: 3)"
  echo "  MAX_TOKENS    Max tokens per run (default: 1800)"
  echo "  TEMPERATURE   Sampling temperature (default: 0.2)"
  echo "  PYTHON        Python command (default: python)"
  exit 2
fi

CARD="$1"
RUN_DIR="$2"

if [[ -z "${HF_TOKEN:-}" ]]; then
  echo "Error: HF_TOKEN is not set." >&2
  exit 1
fi

if [[ ! -f "$CARD" ]]; then
  echo "Error: card not found: $CARD" >&2
  exit 1
fi

DOMAIN_ROOT="$ROOT/domains/${DOMAIN}-domain"
DOMAIN_PACKAGE="${DOMAIN}_domain"
ORACLE_CONTEXT="$DOMAIN_ROOT/src/$DOMAIN_PACKAGE/prompts/oracle_context.txt"
REGISTRY_MODULE="$DOMAIN_PACKAGE.registry:HELPER_REGISTRY"

if [[ ! -f "$ORACLE_CONTEXT" ]]; then
  echo "Error: Oracle context not found: $ORACLE_CONTEXT" >&2
  exit 1
fi

if ! [[ "$RUNS" =~ ^[1-9][0-9]*$ ]]; then
  echo "Error: RUNS must be a positive integer." >&2
  exit 1
fi

CANONICAL_DIR="$RUN_DIR/oracle"
SPLIT_DIR="$RUN_DIR/oracle-release"
mkdir -p "$CANONICAL_DIR" "$SPLIT_DIR"

run_oracle() {
  local profile="$1"
  local output_dir="$2"
  shift 2

  "$PYTHON" -m golden_axe.cli run \
    --card "$CARD" \
    --registry-module "$REGISTRY_MODULE" \
    --profile "$profile" \
    --oracle-output-contract "$ORACLE_OUTPUT_CONTRACT" \
    --model "$MODEL" \
    --hf-token "$HF_TOKEN" \
    --max-tokens "$MAX_TOKENS" \
    --temperature "$TEMPERATURE" \
    --runs "$RUNS" \
    --run-dir "$output_dir" \
    "$@"
}

echo "Model:        $MODEL"
echo "Domain:       $DOMAIN"
echo "Runs/profile: $RUNS"
echo "Card:         $CARD"
echo "Output root:  $RUN_DIR"
echo

echo "[1/2] Running $CANONICAL_PROFILE"
run_oracle "$CANONICAL_PROFILE" "$CANONICAL_DIR"

echo
echo "[2/2] Running $SPLIT_PROFILE"
run_oracle \
  "$SPLIT_PROFILE" \
  "$SPLIT_DIR" \
  --oracle-context "$ORACLE_CONTEXT"

COMPARISON_OUTPUT="$RUN_DIR/comparison.txt"

{
  echo "===== $CANONICAL_PROFILE ====="
  for ((index = 1; index <= RUNS; index++)); do
    response="$(printf '%s/response_%03d.txt' "$CANONICAL_DIR" "$index")"
    echo
    printf '%s\n' "----- RUN $index -----"
    echo
    sed -n '1,$p' "$response"
  done

  echo
  split_label="$(printf "%s" "$SPLIT_PROFILE" | tr "[:lower:]" "[:upper:]")"
  echo "===== $split_label ====="
  for ((index = 1; index <= RUNS; index++)); do
    response="$(printf '%s/response_%03d.txt' "$SPLIT_DIR" "$index")"
    echo
    printf '%s\n' "----- RUN $index -----"
    echo
    sed -n '1,$p' "$response"
  done
  echo
} > "$COMPARISON_OUTPUT"

echo
echo "Completed."
last_response="$(printf "response_%03d.txt" "$RUNS")"
echo "Legacy:    $CANONICAL_DIR/response_001.txt ... $CANONICAL_DIR/$last_response"
echo "Release:   $SPLIT_DIR/response_001.txt ... $SPLIT_DIR/$last_response"
echo "Combined:  $COMPARISON_OUTPUT"
