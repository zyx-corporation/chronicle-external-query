#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORKFLOW_DIR="${ROOT_DIR}/.github/workflows"
DEFAULT_EVENT_FILE="${ROOT_DIR}/.github/act/release-dispatch.event.json"
DOCKER_DESKTOP_BIN="/Applications/Docker.app/Contents/Resources/bin"

ACT_BIN="${ACT_BIN:-}"
if [[ -z "${ACT_BIN}" ]]; then
  if command -v act >/dev/null 2>&1; then
    ACT_BIN="$(command -v act)"
  elif [[ -x /opt/homebrew/bin/act ]]; then
    ACT_BIN="/opt/homebrew/bin/act"
  else
    echo "act command not found on PATH and /opt/homebrew/bin/act is unavailable" >&2
    exit 1
  fi
fi

if [[ -d "${DOCKER_DESKTOP_BIN}" ]]; then
  case ":$PATH:" in
    *":${DOCKER_DESKTOP_BIN}:"*) ;;
    *) export PATH="${DOCKER_DESKTOP_BIN}:$PATH" ;;
  esac
fi

usage() {
  cat <<'EOF'
Usage:
  bash scripts/run_local_act.sh ci
  bash scripts/run_local_act.sh release-verify
  bash scripts/run_local_act.sh release-notes

Environment:
  ACT_EVENT_FILE=/path/to/event.json   Override workflow_dispatch event payload.
EOF
}

MODE="${1:-}"
EVENT_FILE="${ACT_EVENT_FILE:-$DEFAULT_EVENT_FILE}"

case "${MODE}" in
  ci)
    exec "${ACT_BIN}" -W "${WORKFLOW_DIR}/ci.yml" -j test
    ;;
  release-verify)
    exec "${ACT_BIN}" workflow_dispatch \
      -W "${WORKFLOW_DIR}/release.yml" \
      -e "${EVENT_FILE}" \
      -j verify
    ;;
  release-notes)
    exec "${ACT_BIN}" workflow_dispatch \
      -W "${WORKFLOW_DIR}/release.yml" \
      -e "${EVENT_FILE}" \
      -j build-release-notes
    ;;
  release-publish)
    echo "release-publish is not supported under local act because artifact handoff and GitHub release publication stay GitHub-hosted" >&2
    echo "Use bash scripts/run_local_act.sh release-verify plus scripts/generate_release_notes.py for local rehearsal." >&2
    exit 2
    ;;
  ""|-h|--help|help)
    usage
    ;;
  *)
    echo "Unknown mode: ${MODE}" >&2
    usage >&2
    exit 1
    ;;
esac
