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
pytest
chronicle-external-query validate-bundle tests/fixtures/query_engine_bundle/minimal_cli_bundle --json
chronicle-external-query show-bundle tests/fixtures/query_engine_bundle/minimal_cli_bundle --json
chronicle-external-query run-query tests/fixtures/query_engine_bundle/minimal_cli_bundle --query "fixture bundle" --mode graph --json
chronicle-external-query run-query tests/fixtures/query_engine_bundle/minimal_cli_bundle --query "fixture bundle" --mode graph --output trial-artifact.json --json
chronicle-external-query render-artifact-report trial-artifact.json --output trial-report.md --json
chronicle-external-query render-comparison-report trial-artifact.json trial-artifact.json --output comparison-report.md --json
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
- no Chronicle write-back occurs from this repository
