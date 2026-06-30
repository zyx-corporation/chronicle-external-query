# Development Workflow

This workflow adapts Chronicle Stack's ADR discipline for the
`chronicle-external-query` downstream runtime repository.

## Development Gate

Before starting any non-trivial implementation slice, prepare:

1. a scoped issue or milestone-aligned task
2. a branch created from current `main`
3. initial tests or test notes
4. a statement of boundary assumptions
5. explicit non-goals for the slice

The goal is to keep runtime experimentation useful without letting informal
prototype behavior become an accidental contract.

## Recommended Branching

- branch from `main`
- use `codex/<topic>` or another short descriptive branch name
- keep one milestone slice per branch when possible

## Change Sequence

Recommended order for most changes:

1. define or update the contract and boundary expectation
2. add or update tests
3. implement the narrowest code needed to satisfy the test
4. update docs that describe the changed behavior
5. run local verification before commit

## Slice Types

### Contract ingest slices

Focus on:

- file presence
- schema/object shape validation
- version checks
- readable import-validation failures

### Retrieval slices

Focus on:

- retrieval quality changes
- provenance payload changes
- graph/vector/hybrid composition boundaries

### Runtime slices

Focus on:

- answer assembly
- metadata visibility
- deterministic behavior where possible
- evaluation comparability across runs

### Packaging slices

Focus on:

- CLI entrypoints
- CI checks
- release workflows
- release-note generation
- operator setup
- reproducible local runs

## Documentation Expectations

Update the relevant document when behavior changes:

- `docs/architecture.md` for layer responsibilities
- `docs/roadmap.md` for milestone movement
- `docs/testing-strategy.md` for validation coverage changes
- `docs/i18n-strategy.md` for user-facing wording and locale changes
- `docs/releases/` for release automation and release evidence changes
- `docs/adr/` when a boundary decision becomes architectural

## Pull Request Checklist

Before opening a PR, confirm:

- tests cover the changed contract or behavior
- README or supporting docs reflect the current setup
- downstream-derived behavior is not presented as Chronicle-authoritative
- any new user-facing text follows the i18n strategy
- any new dependency is justified by scope and boundary
