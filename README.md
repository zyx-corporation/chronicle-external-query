# chronicle-external-query

`chronicle-external-query` is a downstream derived consumer for Chronicle Stack.
It reads Chronicle-generated handoff bundles and keeps query/runtime execution
outside Chronicle's primary-record boundary.

Japanese README: [README.ja.md](README.ja.md)

## Boundary

- Chronicle `.chronicle/chronicle.jsonl` remains authoritative
- this repository consumes derived exports and handoff contracts
- no writes back to Chronicle are performed implicitly
- graph/vector/query runtime concerns live here, not in Chronicle core

## Current Scope

This repository currently provides:

- loading for real Chronicle handoff bundle directories
- contract-version, required-file, and required-key validation
- graph export loading
- adapter skeleton loading
- sanitized real-bundle fixtures for contract tests
- graph-only and hybrid retrieval result scaffolding with shared provenance,
  overlap tracking, and provider-neutral vector seams

## Repository Layout

```text
chronicle-external-query/
  docs/
  contracts/
    chronicle/
  src/chronicle_external_query/
    ingest/
    retrieval/
    runtime/
    evaluation/
  tests/
```

## Documentation

- [Architecture](docs/architecture.md)
- [Roadmap](docs/roadmap.md)
- [Extension Roadmap](docs/extension-roadmap.md)
- [Pluggable Extension Spec](docs/pluggable-extension-spec.md)
- [Coding Guidelines](docs/coding-guidelines.md)
- [Development Workflow](docs/development-workflow.md)
- [Testing Strategy](docs/testing-strategy.md)
- [Retrieval Contract](docs/retrieval-contract.md)
- [Runtime Answer Contract](docs/runtime-answer-contract.md)
- [Chronicle Trial Alignment](docs/chronicle-trial-alignment.md)
- [Clean Checkout](docs/clean-checkout.md)
- [Operator Runbook](docs/operator-runbook.md)
- [i18n Strategy](docs/i18n-strategy.md)
- [ADR Index](docs/adr/README.md)

## Local Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

One-command baseline smoke:

```bash
bash scripts/smoke_clean_checkout.sh
```

If your default `python3` is older than 3.11, set `PYTHON_BIN` explicitly, for
example `PYTHON_BIN=/usr/local/bin/python3.11 bash scripts/smoke_clean_checkout.sh`.

## Local CLI

```bash
chronicle-external-query validate-bundle /path/to/handoff-bundle --json
chronicle-external-query show-bundle /path/to/handoff-bundle --json
chronicle-external-query run-query /path/to/handoff-bundle --query "release planning context" --mode graph --json
chronicle-external-query render-artifact-report trial-artifact.json --output trial-report.md --json
chronicle-external-query render-comparison-report first-artifact.json second-artifact.json --output comparison-report.md --json
```

## CI Baseline

```bash
bash scripts/smoke_clean_checkout.sh
```

The same baseline runs in GitHub Actions on pushes and pull requests to `main`.

## Release Status

The first supported local downstream runtime baseline is documented in
[docs/releases/v0.2.0-first-supported-baseline.md](docs/releases/v0.2.0-first-supported-baseline.md).
