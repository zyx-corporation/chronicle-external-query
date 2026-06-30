#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORKFLOW_DIR="${ROOT_DIR}/.github/workflows"
DEFAULT_EVENT_FILE="${ROOT_DIR}/.github/act/release-dispatch.event.json"
DOCKER_DESKTOP_BIN="${DOCKER_DESKTOP_BIN:-/Applications/Docker.app/Contents/Resources/bin}"

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
  bash scripts/run_local_act.sh doctor
  bash scripts/run_local_act.sh ci
  bash scripts/run_local_act.sh all
  bash scripts/run_local_act.sh release-verify
  bash scripts/run_local_act.sh release-notes
  bash scripts/run_local_act.sh <mode> -- [extra act args]

Environment:
  ACT_EVENT_FILE=/path/to/event.json   Override workflow_dispatch event payload.
  ACT_ARGS="..."                       Extra arguments appended to every act invocation.
EOF
}

MODE="${1:-}"
EVENT_FILE="${ACT_EVENT_FILE:-$DEFAULT_EVENT_FILE}"
shift || true

EXTRA_ARGS=()
if [[ "${1:-}" == "--" ]]; then
  shift
  EXTRA_ARGS=("$@")
fi

if [[ -n "${ACT_ARGS:-}" ]]; then
  # shellcheck disable=SC2206
  ACT_ARGS_ARRAY=(${ACT_ARGS})
else
  ACT_ARGS_ARRAY=()
fi

ACT_PREFIX=("${ACT_BIN}")
if [[ ${#ACT_ARGS_ARRAY[@]} -gt 0 ]]; then
  ACT_PREFIX+=("${ACT_ARGS_ARRAY[@]}")
fi
if [[ ${#EXTRA_ARGS[@]} -gt 0 ]]; then
  ACT_PREFIX+=("${EXTRA_ARGS[@]}")
fi

doctor() {
  echo "act_bin=${ACT_BIN}"
  "${ACT_BIN}" --version

  if command -v docker >/dev/null 2>&1; then
    echo "docker_bin=$(command -v docker)"
    docker --version
  elif [[ -x "${DOCKER_DESKTOP_BIN}/docker" ]]; then
    echo "docker_bin=${DOCKER_DESKTOP_BIN}/docker"
    "${DOCKER_DESKTOP_BIN}/docker" --version
  else
    echo "docker not found on PATH or Docker Desktop bin" >&2
    return 1
  fi

  if command -v docker-credential-desktop >/dev/null 2>&1; then
    echo "docker_credential_helper=$(command -v docker-credential-desktop)"
  elif [[ -x "${DOCKER_DESKTOP_BIN}/docker-credential-desktop" ]]; then
    echo "docker_credential_helper=${DOCKER_DESKTOP_BIN}/docker-credential-desktop"
  else
    echo "docker-credential-desktop not found; docker auth-backed pulls may fail" >&2
    return 1
  fi

  if [[ -f "${EVENT_FILE}" ]]; then
    echo "act_event_file=${EVENT_FILE}"
  else
    echo "ACT event file not found: ${EVENT_FILE}" >&2
    return 1
  fi
}

case "${MODE}" in
  doctor)
    doctor
    ;;
  ci)
    exec "${ACT_PREFIX[@]}" -W "${WORKFLOW_DIR}/ci.yml" -j test
    ;;
  all)
    doctor
    "${ACT_PREFIX[@]}" -W "${WORKFLOW_DIR}/ci.yml" -j test
    exec "${ACT_PREFIX[@]}" workflow_dispatch \
      -W "${WORKFLOW_DIR}/release.yml" \
      -e "${EVENT_FILE}" \
      -j build-release-notes
    ;;
  release-verify)
    exec "${ACT_PREFIX[@]}" workflow_dispatch \
      -W "${WORKFLOW_DIR}/release.yml" \
      -e "${EVENT_FILE}" \
      -j verify
    ;;
  release-notes)
    exec "${ACT_PREFIX[@]}" workflow_dispatch \
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
