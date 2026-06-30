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
runs `pytest`, validates the minimal fixture bundle, and exercises a
representative hybrid query plus markdown report rendering.

If your default `python3` is older than 3.11, set `PYTHON_BIN` explicitly when
running the script:

```bash
PYTHON_BIN=/usr/local/bin/python3.11 bash scripts/smoke_clean_checkout.sh
```

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
