#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT_FILE="${ROOT_DIR}/.env.local.plugins"
OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://127.0.0.1:11434}"
FORCE="${1:-}"

if [[ -f "${OUTPUT_FILE}" && "${FORCE}" != "--force" ]]; then
  echo "${OUTPUT_FILE} already exists. Re-run with --force to overwrite." >&2
  exit 1
fi

if ! command -v curl >/dev/null 2>&1; then
  echo "curl is required to detect local gemma4 models" >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required to parse local Ollama model metadata" >&2
  exit 1
fi

MODEL_JSON="$(curl -fsS "${OLLAMA_BASE_URL}/v1/models" || true)"
if [[ -z "${MODEL_JSON}" ]]; then
  echo "Could not read ${OLLAMA_BASE_URL}/v1/models. Is the local Ollama runtime running?" >&2
  exit 1
fi

GEMMA4_MODEL="$(
  MODEL_JSON="${MODEL_JSON}" python3 - <<'PY'
import json
import os
import sys

payload = json.loads(os.environ["MODEL_JSON"])
for entry in payload.get("data", []):
    model_id = str(entry.get("id", "")).strip()
    if model_id.startswith("gemma4"):
        print(model_id)
        sys.exit(0)

raise SystemExit("no gemma4 model found in local Ollama /v1/models response")
PY
)"

cat > "${OUTPUT_FILE}" <<EOF
export GEMMA4_ENABLED=true
export GEMMA4_BASE_URL=${OLLAMA_BASE_URL}
export GEMMA4_MODEL=${GEMMA4_MODEL}
export GEMMA4_TIMEOUT=30
# export GEMMA4_API_KEY=

export OPENAI_COMPATIBLE_HOSTED_ENABLED=false
export OPENAI_COMPATIBLE_HOSTED_BASE_URL=https://api.openai.com
export OPENAI_COMPATIBLE_HOSTED_MODEL=
export OPENAI_COMPATIBLE_HOSTED_API_KEY=
export OPENAI_COMPATIBLE_HOSTED_TIMEOUT=30
EOF

echo "Wrote ${OUTPUT_FILE}"
echo "Next:"
echo "  source ${OUTPUT_FILE}"
echo "  .venv/bin/chronicle-external-query doctor-plugin gemma4 --json"
echo "  .venv/bin/chronicle-external-query run-query tests/fixtures/query_engine_bundle/minimal_cli_bundle --query 'fixture bundle' --mode graph --answer-plugin gemma4 --json"
