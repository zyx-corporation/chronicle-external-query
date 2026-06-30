# Testing Strategy

This document defines how `chronicle-external-query` validates downstream
bundle ingest, retrieval, runtime behavior, and evaluation outputs.

## Testing Goals

- protect Chronicle-facing contract boundaries
- detect structural drift before runtime work begins
- keep retrieval and runtime behavior explainable
- make provenance-preservation failures easy to catch
- ensure evaluation outputs are repeatable enough for review

## Primary Principles

- test contract ingest before optimizing runtime behavior
- prefer deterministic fixtures for bundle loading and retrieval assertions
- add regression coverage for every meaningful bug or contract drift issue
- treat provenance and uncertainty handling as testable behavior

## Test Categories

### Unit tests

Use for:

- JSON and JSONL parsing helpers
- object-shape validation helpers
- ranking functions
- prompt/context builders
- metadata serializers

### Contract tests

Use for stable bundle and output boundaries:

- required Chronicle bundle files
- `query_engine_handoff.json` shape expectations
- `graph.json` version and object expectations
- `bundle_manifest.json` required fields
- runtime answer metadata keys
- evaluation serialization format
- evaluation artifact malformed-JSON, required-key, and field-shape validation
- evaluation artifact list-entry validation for reviewed files and match objects

### Fixture tests

Use for representative Chronicle bundle examples:

- minimal valid bundle
- malformed bundle
- contract-version mismatch bundle
- bundle with incomplete graph export
- bundle with no retrieval matches

Real Chronicle-generated fixtures should be added as soon as Milestone A
hardening begins. A sanitized minimal CLI-generated bundle fixture and a more
representative sanitized CLI-generated bundle fixture are now part of the
repository baseline, and additional fixtures should expand from there.
Milestone F adds a fixture registry so future fixture growth can be opt-in and
manifest-driven without weakening the committed baseline path.
Milestone G adds provider plugin gating so credentialed or provider-backed
tests remain opt-in and cannot silently join the default baseline.

### Retrieval tests

Use for:

- graph-only matching behavior
- hybrid retrieval composition
- provenance payload shape
- overlap and vector-only merge behavior
- stable ordering and tie-breaking rules
- empty-result handling
- representative Chronicle-derived bundle regression coverage

### Runtime tests

Use for:

- answer metadata
- prompt/context assembly
- result serialization
- deterministic no-provider fallback behavior
- representative query regression and repeated-run comparison stability

### Regression tests

Add whenever:

- a bundle that should load stops loading
- invalid input is accepted silently
- retrieval changes lose provenance
- runtime output changes shape unexpectedly

### T-RDE-style downstream tests

Adapted from Chronicle Stack's T-RDE discipline, these tests ask:

1. what provenance is preserved?
2. what downstream interpretation is added?
3. what uncertainty remains visible?
4. what unsupported claim must not be introduced?

Examples:

- retrieval must not imply source certainty beyond the exported data
- runtime metadata must distinguish graph-only results from hybrid results
- evaluation output must not imply Chronicle acceptance or review completion
- malformed bundles must not be treated as partially authoritative success

## Local Verification

Current local baseline:

```bash
pip install -e ".[dev]"
pytest
chronicle-external-query validate-bundle tests/fixtures/query_engine_bundle/minimal_cli_bundle --json
chronicle-external-query show-bundle tests/fixtures/query_engine_bundle/minimal_cli_bundle --json
chronicle-external-query list-fixtures --json --no-env-fixture-dirs
chronicle-external-query list-plugins --json
chronicle-external-query run-query tests/fixtures/query_engine_bundle/minimal_cli_bundle --query "fixture bundle" --mode graph --json
```

Current CI smoke also exercises:

- hybrid queries with a local vector fixture
- markdown trial report rendering from a saved artifact
- markdown comparison report rendering from two saved artifacts
- provider-adapter tests behind explicit opt-in markers in the future

Provider plugin opt-in entrypoints:

```bash
pytest --run-provider-plugins tests/providers/
pytest --run-hosted-providers -m hosted_provider
```

## Test Data Rules

- keep small synthetic fixtures in the repo for deterministic tests
- prefer copied or reduced real Chronicle bundle fixtures for contract tests
- sanitize any fixture content before committing if it originates from real
  records
- register optional fixture packs through `fixture-pack.json` manifests instead
  of hardcoding new fixture trees into the default baseline
- register provider credentials only through plugin-specific environment
  variables, not through baseline package imports or shared config files

## Coverage Expectations

Minimum expectation for a behavior-changing PR:

- one test proving the intended path
- one test proving a nearby failure path when applicable
- one regression test for any bug fix or drift correction
