#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

run_tests() {
  local package="$1"
  PYTHONPATH="${ROOT}/${package}/src" \
    python -m unittest discover -s "${ROOT}/${package}/tests" -q
}

run_tests "packages/helper-selector"
run_tests "packages/golden-axe-oracle"
run_tests "packages/critique-pipeline"
run_tests "backends/code-generator"

PYTHONPATH="${ROOT}/packages/helper-selector/src:${ROOT}/domains/lhco-domain/src" \
  python -m unittest discover -s "${ROOT}/domains/lhco-domain/tests" -q

PYTHONPATH="${ROOT}/packages/workbench-contracts/src:${ROOT}/packages/helper-selector/src:${ROOT}/domains/dummy-domain/src" \
  python -m unittest discover -s "${ROOT}/domains/dummy-domain/tests" -q

PYTHONPATH="${ROOT}/packages/workbench-contracts/src:${ROOT}/packages/helper-selector/src:${ROOT}/packages/critique-pipeline/src:${ROOT}/backends/code-generator/src:${ROOT}/domains/dummy-domain/src:${ROOT}/workflows/src" \
  python -m unittest discover -s "${ROOT}/workflows/tests" -q

PYTHONPATH="${ROOT}/packages/workbench-contracts/src:${ROOT}/packages/helper-selector/src:${ROOT}/packages/golden-axe-oracle/src:${ROOT}/packages/critique-pipeline/src:${ROOT}/backends/code-generator/src:${ROOT}/domains/lhco-domain/src:${ROOT}/domains/dummy-domain/src:${ROOT}/workflows/src" \
  python -m unittest discover -s "${ROOT}/tests" -q

echo "All tests passed."
