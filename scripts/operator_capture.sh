#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${VENV_DIR:-${ROOT_DIR}/.venv}"
BUNDLE_DIR="${1:-tests/fixtures/query_engine_bundle/representative_cli_bundle}"
OUTPUT_DIR="${2:-/tmp/chronicle-external-query-operator-capture}"
VECTOR_FIXTURE="${VECTOR_FIXTURE:-tests/fixtures/vector_matches/representative-vector-matches.json}"
QUERY_TEXT="${QUERY_TEXT:-release planning follow-up context}"
DRY_RUN="${DRY_RUN:-0}"

run() {
  if [ "${DRY_RUN}" = "1" ]; then
    printf '[operator-capture] dry-run: %q' "$1"
    shift || true
    for arg in "$@"; do
      printf ' %q' "${arg}"
    done
    printf '\n'
    return 0
  fi
  "$@"
}

run_stdout_to_file() {
  local output_path="$1"
  shift
  if [ "${DRY_RUN}" = "1" ]; then
    printf '[operator-capture] dry-run: %q' "$1"
    shift || true
    for arg in "$@"; do
      printf ' %q' "${arg}"
    done
    printf ' > %q\n' "${output_path}"
    return 0
  fi
  "$@" > "${output_path}"
}

usage() {
  cat <<'EOF'
Usage:
  bash scripts/operator_capture.sh [BUNDLE_DIR] [OUTPUT_DIR]

Behavior:
  - validates a bundle
  - captures bundle summary JSON
  - runs a representative hybrid query
  - saves an artifact and markdown trial report under OUTPUT_DIR

Environment:
  VENV_DIR        Override the virtualenv directory
  DRY_RUN=1       Print commands without executing
  VECTOR_FIXTURE  Override the vector fixture path
  QUERY_TEXT      Override the query text
EOF
}

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  usage
  exit 0
fi

cd "${ROOT_DIR}"

if [ ! -x "${VENV_DIR}/bin/chronicle-external-query" ]; then
  echo "Expected ${VENV_DIR}/bin/chronicle-external-query. Run bash scripts/operator_preflight.sh first." >&2
  exit 1
fi

run mkdir -p "${OUTPUT_DIR}"

VALIDATE_JSON="${OUTPUT_DIR}/validate-bundle.json"
SHOW_JSON="${OUTPUT_DIR}/show-bundle.json"
ARTIFACT_JSON="${OUTPUT_DIR}/trial-artifact.json"
RUN_QUERY_JSON="${OUTPUT_DIR}/run-query.json"
TRIAL_REPORT_MD="${OUTPUT_DIR}/trial-report.md"
REPORT_JSON="${OUTPUT_DIR}/render-artifact-report.json"

run_stdout_to_file "${VALIDATE_JSON}" \
  "${VENV_DIR}/bin/chronicle-external-query" validate-bundle "${BUNDLE_DIR}" --json

run_stdout_to_file "${SHOW_JSON}" \
  "${VENV_DIR}/bin/chronicle-external-query" show-bundle "${BUNDLE_DIR}" --json

run_stdout_to_file "${RUN_QUERY_JSON}" \
  "${VENV_DIR}/bin/chronicle-external-query" run-query "${BUNDLE_DIR}" \
  --query "${QUERY_TEXT}" \
  --mode hybrid \
  --vector-fixture "${VECTOR_FIXTURE}" \
  --output "${ARTIFACT_JSON}" \
  --json

run_stdout_to_file "${REPORT_JSON}" \
  "${VENV_DIR}/bin/chronicle-external-query" render-artifact-report "${ARTIFACT_JSON}" \
  --output "${TRIAL_REPORT_MD}" \
  --json

if [ "${DRY_RUN}" != "1" ]; then
  printf '%s\n' "${OUTPUT_DIR}"
fi
