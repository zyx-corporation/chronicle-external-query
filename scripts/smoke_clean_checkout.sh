#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"

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

PYTHON_BIN="$(resolve_python_bin)"

cd "${ROOT_DIR}"

if [ ! -x "${VENV_DIR}/bin/python" ]; then
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
fi

"${VENV_DIR}/bin/python" -m pip install --upgrade pip
"${VENV_DIR}/bin/pip" install -e ".[dev]"

"${VENV_DIR}/bin/pytest" -q
"${VENV_DIR}/bin/chronicle-external-query" validate-bundle tests/fixtures/query_engine_bundle/minimal_cli_bundle --json
"${VENV_DIR}/bin/chronicle-external-query" show-bundle tests/fixtures/query_engine_bundle/minimal_cli_bundle --json
"${VENV_DIR}/bin/chronicle-external-query" run-query tests/fixtures/query_engine_bundle/minimal_cli_bundle --query "fixture bundle" --mode graph --json
"${VENV_DIR}/bin/chronicle-external-query" run-query tests/fixtures/query_engine_bundle/representative_cli_bundle --query "release planning follow-up context" --mode hybrid --vector-fixture tests/fixtures/vector_matches/representative-vector-matches.json --output /tmp/chronicle-representative-artifact.json --json
"${VENV_DIR}/bin/chronicle-external-query" render-artifact-report /tmp/chronicle-representative-artifact.json --output /tmp/chronicle-representative-trial-report.md --json
"${VENV_DIR}/bin/chronicle-external-query" render-comparison-report /tmp/chronicle-representative-artifact.json /tmp/chronicle-representative-artifact.json --output /tmp/chronicle-representative-comparison-report.md --json
