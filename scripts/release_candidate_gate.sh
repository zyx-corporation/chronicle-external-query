#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_OPTIONAL_PLUGIN_MATRIX="${RUN_OPTIONAL_PLUGIN_MATRIX:-0}"

cd "${ROOT_DIR}"

bash scripts/smoke_clean_checkout.sh
PYTHONPATH=src .venv/bin/python scripts/check_plugin_compatibility.py > /tmp/chronicle-plugin-compatibility.json

if [ "${RUN_OPTIONAL_PLUGIN_MATRIX}" = "1" ]; then
  .venv/bin/pytest -q --run-provider-plugins --run-gemma4 tests/providers/test_gemma4_plugin.py || true
  .venv/bin/pytest -q --run-provider-plugins --run-hosted-providers tests/providers/test_openai_compatible_hosted_plugin.py || true
fi
