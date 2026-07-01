#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${VENV_DIR:-${ROOT_DIR}/.venv}"
DRY_RUN="${DRY_RUN:-0}"
BUNDLE_DIR="${BUNDLE_DIR:-tests/fixtures/query_engine_bundle/representative_cli_bundle}"
VECTOR_FIXTURE="${VECTOR_FIXTURE:-tests/fixtures/vector_matches/representative-vector-matches.json}"
QUERY_TEXT="${QUERY_TEXT:-release planning follow-up context}"
ARTIFACT_PATH="${ARTIFACT_PATH:-/tmp/chronicle-external-query-operator-preflight-artifact.json}"
REPORT_PATH="${REPORT_PATH:-/tmp/chronicle-external-query-operator-preflight-report.md}"

run() {
  if [ "${DRY_RUN}" = "1" ]; then
    printf '[operator-preflight] dry-run: %q' "$1"
    shift || true
    for arg in "$@"; do
      printf ' %q' "${arg}"
    done
    printf '\n'
    return 0
  fi
  "$@"
}

resolve_python_bin() {
  if [ -n "${PYTHON_BIN:-}" ]; then
    printf '%s\n' "${PYTHON_BIN}"
    return
  fi

  for candidate in \
    python3.12 \
    python3.11 \
    python3 \
    /opt/homebrew/bin/python3 \
    /opt/homebrew/bin/python3.14 \
    /usr/local/bin/python3.11 \
    /usr/local/bin/python3 \
    /Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11 \
    /Library/Frameworks/Python.framework/Versions/Current/bin/python3; do
    if command -v "${candidate}" >/dev/null 2>&1 || [ -x "${candidate}" ]; then
      "${candidate}" - <<'PY' >/dev/null 2>&1
import sys
raise SystemExit(0 if sys.version_info >= (3, 11) else 1)
PY
      if [ $? -eq 0 ]; then
        printf '%s\n' "${candidate}"
        return
      fi
    fi
  done

  echo "No Python 3.11+ interpreter was found. Set PYTHON_BIN explicitly." >&2
  exit 1
}

usage() {
  cat <<'EOF'
Usage:
  bash scripts/operator_preflight.sh

Behavior:
  - ensures a local .venv exists
  - installs the current checkout in editable mode
  - runs pytest
  - validates the representative Chronicle bundle fixture
  - runs a representative hybrid query and renders a markdown report

Environment:
  VENV_DIR        Override the virtualenv directory
  PYTHON_BIN     Override the Python 3.11+ interpreter
  DRY_RUN=1      Print commands without executing
  BUNDLE_DIR     Override the representative bundle fixture directory
  VECTOR_FIXTURE Override the representative vector fixture path
  QUERY_TEXT     Override the representative query text
  ARTIFACT_PATH  Override the generated artifact path
  REPORT_PATH    Override the generated markdown report path
EOF
}

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  usage
  exit 0
fi

PYTHON_BIN="$(resolve_python_bin)"

cd "${ROOT_DIR}"

if [ ! -x "${VENV_DIR}/bin/python" ]; then
  run "${PYTHON_BIN}" -m venv "${VENV_DIR}"
fi

run "${VENV_DIR}/bin/python" -m pip install --upgrade pip
run "${VENV_DIR}/bin/pip" install -e ".[dev]"

run "${VENV_DIR}/bin/pytest" -q
run "${VENV_DIR}/bin/chronicle-external-query" validate-bundle "${BUNDLE_DIR}" --json
run "${VENV_DIR}/bin/chronicle-external-query" run-query "${BUNDLE_DIR}" \
  --query "${QUERY_TEXT}" \
  --mode hybrid \
  --vector-fixture "${VECTOR_FIXTURE}" \
  --output "${ARTIFACT_PATH}" \
  --json
run "${VENV_DIR}/bin/chronicle-external-query" render-artifact-report "${ARTIFACT_PATH}" \
  --output "${REPORT_PATH}" \
  --json
