# Architecture

`chronicle-external-query` sits downstream from Chronicle Stack and only consumes
derived bundle outputs.

## Inputs

- Chronicle handoff bundle directories
- `query_engine_handoff.json`
- `graph.json`
- `bundle_manifest.json`
- `query_engine_adapter_skeleton.json`
- acceptance checklist and trial-template files
- optional access to the Chronicle primary record path referenced by bundle metadata

## Internal Layers

- `ingest/`: file loading and structural validation
- `retrieval/`: graph/vector/hybrid retrieval implementations, provider-neutral vector seams, and shared provenance payloads
- `runtime/`: ranking, prompt construction, answer orchestration
- `evaluation/`: trial serialization and repeatable evaluation helpers

## Output Direction

This repository can produce local evaluation artifacts or runtime responses, but
it should not mutate Chronicle primary records directly.

## Authority Boundary

- Chronicle primary records remain authoritative
- handoff bundles remain derived downstream inputs
- local evaluation artifacts and plugin-backed comparisons remain
  non-authoritative review support
- no Chronicle write-back path exists in this repository

See also:

- [Chronicle Trial Alignment](chronicle-trial-alignment.md)
- [Chronicle Write-back Boundary](chronicle-writeback-boundary.md)
- [ADR-003](adr/ADR-003-chronicle-writeback-remains-out-of-scope.md)
