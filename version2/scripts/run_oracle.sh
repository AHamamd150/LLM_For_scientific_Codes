#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

MODEL="${MODEL:-Qwen/Qwen3-14B}"
RUNS="${RUNS:-1}"
MAX_TOKENS="${MAX_TOKENS:-1800}"
TEMPERATURE="${TEMPERATURE:-0.2}"
PYTHON="${PYTHON:-python}"
DOMAIN="${DOMAIN:-lhco}"
PROFILE="${PROFILE:-oracle}"
ORACLE_OUTPUT_CONTRACT="${ORACLE_OUTPUT_CONTRACT:-auto}"

PACKAGE_PATHS=(
  "$ROOT/packages/workbench-contracts/src"
  "$ROOT/packages/helper-selector/src"
  "$ROOT/packages/golden-axe-oracle/src"
  "$ROOT/packages/critique-pipeline/src"
  "$ROOT/backends/code-generator/src"
  "$ROOT/domains/${DOMAIN}-domain/src"
  "$ROOT/workflows/src"
)

PACKAGE_PYTHONPATH="$(IFS=:; echo "${PACKAGE_PATHS[*]}")"
export PYTHONPATH="$PACKAGE_PYTHONPATH${PYTHONPATH:+:$PYTHONPATH}"

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 CARD RUN_DIR"
  echo
  echo "Environment variables:"
  echo "  HF_TOKEN      Hugging Face access token (required)"
  echo "  MODEL         Model ID  (default: Qwen/Qwen3-14B)"
  echo "  DOMAIN        Domain name without '-domain' suffix (default: lhco)"
  echo "  PROFILE       Oracle profile (default: oracle)"
  echo "  ORACLE_OUTPUT_CONTRACT  auto, system, domain, or none (default: auto)"
  echo "  RUNS          Number of oracle runs (default: 1)"
  echo "  MAX_TOKENS    Max tokens per run (default: 1800)"
  echo "  TEMPERATURE   Sampling temperature (default: 0.2)"
  echo
  echo "Oracle output is written to RUN_DIR/response_NNN.txt"
  echo "Review the output and revise CARD before running the main pipeline."
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

ORACLE_CONTEXT=""
REGISTRY_MODULE="${DOMAIN}_domain.registry:HELPER_REGISTRY"
CONTEXT_ARGS=()

case "$PROFILE" in
  oracle|oracle-split-v3)
    ORACLE_CONTEXT="$ROOT/domains/${DOMAIN}-domain/src/${DOMAIN}_domain/prompts/oracle_context.txt"
    ;;
  oraclet)
    ORACLE_CONTEXT="$ROOT/domains/${DOMAIN}-domain/src/${DOMAIN}_domain/prompts/oraclet_domain_prompt.txt"
    ;;
esac

if [[ -n "$ORACLE_CONTEXT" ]]; then
  if [[ ! -f "$ORACLE_CONTEXT" ]]; then
    echo "Error: Oracle context not found: $ORACLE_CONTEXT" >&2
    exit 1
  fi
  CONTEXT_ARGS=(--oracle-context "$ORACLE_CONTEXT")
fi

mkdir -p "$RUN_DIR"

echo "Model:          $MODEL"
echo "Domain:         $DOMAIN"
echo "Profile:        $PROFILE"
echo "Output mode:    $ORACLE_OUTPUT_CONTRACT"
echo "Card:           $CARD"
if [[ ${#CONTEXT_ARGS[@]} -gt 0 ]]; then
  echo "Oracle context: $ORACLE_CONTEXT"
else
  echo "Oracle context: (not used by this profile)"
fi
echo "Runs:           $RUNS"
echo "Run directory:  $RUN_DIR"
echo

CMD=(
  "$PYTHON" -m golden_axe.cli run
  --card "$CARD"
  --registry-module "$REGISTRY_MODULE"
  --profile "$PROFILE"
  --oracle-output-contract "$ORACLE_OUTPUT_CONTRACT"
)

if [[ ${#CONTEXT_ARGS[@]} -gt 0 ]]; then
  CMD+=("${CONTEXT_ARGS[@]}")
fi

CMD+=(
  --model "$MODEL"
  --hf-token "$HF_TOKEN"
  --max-tokens "$MAX_TOKENS"
  --temperature "$TEMPERATURE"
  --runs "$RUNS"
  --run-dir "$RUN_DIR"
)

"${CMD[@]}"

echo
echo "Oracle output: $RUN_DIR/response_001.txt"
echo "Review ambiguities and revise your card before running the main pipeline."
