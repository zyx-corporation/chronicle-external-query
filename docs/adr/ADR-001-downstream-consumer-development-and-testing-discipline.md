# ADR-001: Downstream Consumer Development and Testing Discipline

## Status

Accepted

## Date

2026-06-28

## Related documents

- [Coding Guidelines](../coding-guidelines.md)
- [Development Workflow](../development-workflow.md)
- [Testing Strategy](../testing-strategy.md)
- [Architecture](../architecture.md)
- [Roadmap](../roadmap.md)
- Chronicle Stack `ADR-001: T-RDE, TDD, and Design-Pattern Principles`
- Chronicle Stack `ADR 0087: Downstream Query-Engine Handoff Stays Read-Only`
- Chronicle Stack `ADR 0088: Downstream Import Validation Remains Preview-Only`

## Context

`chronicle-external-query` consumes Chronicle-generated derived bundles and is
intended to host retrieval, runtime, and evaluation behavior outside Chronicle
Stack core. That makes this repository useful, but also easy to over-claim.

If downstream code silently coerces malformed bundles, invents provenance, or
mixes runtime convenience with contract truth, then the repository weakens the
very boundary Chronicle Stack is trying to preserve.

Chronicle Stack already established two important upstream rules:

- the downstream handoff is read-only and non-authoritative over primary records
- import validation should remain structural before any real runtime execution

This repository needs a matching engineering discipline so that experimental
runtime work does not become accidental architecture.

## Decision

`chronicle-external-query` adopts a development discipline based on four rules:

1. contract-first ingest before runtime expansion
2. tests for both behavior and provenance-preservation boundaries
3. explicit seams between ingest, retrieval, runtime, and evaluation layers
4. documentation updates when architectural boundaries change

## Consequences

- bundle validation is treated as a first-class development slice, not setup
  boilerplate
- retrieval and runtime code must preserve the difference between source
  authority and downstream interpretation
- regression tests are required for contract drift and provenance bugs
- provider-specific integrations stay behind explicit interfaces until a later
  ADR accepts tighter coupling

## Non-goals

This ADR does not:

- require every experiment to be feature-complete before being committed
- prohibit prototype code entirely
- decide a specific vector store, graph database, or hosted model provider
- turn this repository into a Chronicle primary-record writer
