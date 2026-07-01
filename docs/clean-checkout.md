# Clean Checkout

This document is the shortest path to reproduce a working
`chronicle-external-query` setup from a fresh clone.

## Fresh Clone

```bash
git clone https://github.com/zyx-corporation/chronicle-external-query.git
cd chronicle-external-query
```

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Verify the Baseline

```bash
bash scripts/smoke_clean_checkout.sh
```

This script creates `.venv` if needed, installs the package in editable mode,
runs `ruff check src tests`, runs `pytest`, validates the minimal fixture
bundle, and exercises a
representative hybrid query plus markdown report rendering.

For same-checkout verification after the first install, you can also run:

```bash
bash scripts/operator_preflight.sh
bash scripts/operator_capture.sh
```

If your default `python3` is older than 3.11, set `PYTHON_BIN` explicitly when
running the script:

```bash
PYTHON_BIN=/usr/local/bin/python3.11 bash scripts/smoke_clean_checkout.sh
```

Set `VENV_DIR=/path/to/.venv` when you want the operator helper scripts to use
an alternate virtualenv location.

## Local Act Rehearsal

If you want to reproduce repository CI and release rehearsal locally:

```bash
bash scripts/run_local_act.sh doctor
bash scripts/run_local_act.sh ci
bash scripts/run_local_act.sh all
bash scripts/run_local_act.sh release-verify-optional
```

Use `doctor` first when `act` cannot find Docker or its credential helper.
Use `all` when you want the CI baseline plus the release workflow through
`build-release-notes` in one command.
Use `ACT_OPTIONAL_EVENT_FILE=...` when you want `release-verify-optional` to
rehearse a different optional-plugin input payload.

## Locale Override

Explicit CLI locale:

```bash
chronicle-external-query validate-bundle tests/fixtures/query_engine_bundle/minimal_cli_bundle --locale en --json
```

Environment fallback:

```bash
export CHRONICLE_EXTERNAL_QUERY_LOCALE=en
chronicle-external-query validate-bundle tests/fixtures/query_engine_bundle/minimal_cli_bundle --json
```

## Expected Boundaries

- validation and query execution are local-only
- default hybrid mode still uses a provider-neutral null vector fallback
- the representative hybrid smoke path uses only checked-in local vector
  fixtures, not a hosted provider
- no Chronicle write-back occurs from this repository
