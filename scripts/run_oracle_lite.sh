#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

export PROFILE="${PROFILE:-oracle_lite}"
export ORACLE_OUTPUT_CONTRACT="${ORACLE_OUTPUT_CONTRACT:-none}"
export MODEL="${MODEL:-Qwen/Qwen3-14B}"
export RUNS="${RUNS:-1}"
export MAX_TOKENS="${MAX_TOKENS:-1800}"
export TEMPERATURE="${TEMPERATURE:-0.2}"

exec "$ROOT/scripts/run_oracle.sh" "$@"
