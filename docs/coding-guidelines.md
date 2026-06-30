# Coding Guidelines

This document defines coding expectations for `chronicle-external-query` as a
downstream derived consumer of Chronicle Stack.

## Guiding Principles

- keep Chronicle primary records authoritative and unchanged
- prefer explicit boundaries over implicit convenience
- keep retrieval, runtime, and evaluation concerns separable
- make provenance and uncertainty visible in code and output shapes
- avoid vendor lock-in at the interface level unless a later ADR accepts it

## Language and Runtime

- target Python 3.11+
- prefer the standard library unless a dependency clearly improves contract
  safety, retrieval quality, or operator ergonomics
- keep core ingest and contract validation paths dependency-light

## Package Structure

Current package layout:

- `ingest/`: bundle loading, file validation, schema/version gates
- `retrieval/`: graph, vector, and hybrid retrieval paths
- `runtime/`: orchestration, ranking, prompt/context composition
- `evaluation/`: result serialization, trial output helpers

Keep responsibilities narrow. If a module starts mixing ingest, retrieval, and
runtime decisions, split it before complexity becomes hidden policy.

## Interface Design

- treat Chronicle bundle files as contracts, not ad hoc inputs
- keep public function signatures explicit and typed
- prefer small dataclasses and typed dictionaries over ambiguous nested payload
  mutation
- use stable field names for response metadata and provenance
- fail fast when contract drift is detected

Recommended:

- return structured errors for missing files, malformed JSON, and version drift
- keep provider-specific adapter interfaces behind small seams
- preserve query, provenance, and validation metadata through each layer

Avoid:

- silently coercing invalid contract shapes
- mutating loaded Chronicle payloads in place
- mixing user-facing wording with core retrieval logic
- burying boundary decisions inside helper functions with weak names

## Error Handling

- raise explicit domain errors for import validation failures
- error messages should explain what is missing, malformed, or unsupported
- do not downgrade contract mismatches into warnings unless the output remains
  explicitly partial and non-authoritative

## Data and Provenance Rules

- do not invent provenance that Chronicle did not provide
- if retrieval adds ranking or supplemental metadata, keep that clearly marked
  as downstream-derived
- preserve a distinction between source record identity and downstream runtime
  interpretation

## Documentation Rule

Any change that alters bundle expectations, retrieval semantics, runtime output
shape, or localization behavior should update the matching docs and ADR links in
the same change when practical.
