# ADR-003: Chronicle Write-back Remains Out of Scope

## Status

Accepted

## Context

`chronicle-external-query` now supports:

- deterministic local validation and smoke execution
- optional fixture expansion
- optional local and hosted answer plugins
- comparative evaluation across baseline and plugin-backed runs
- release automation for the downstream runtime workspace

That increases the amount of downstream-derived review material that can be
produced here. It also raises the question of whether local trial artifacts,
plugin-backed comparisons, or release-time review summaries should ever be
written back into Chronicle itself.

This repository already relies on a strong boundary:

- Chronicle primary records remain authoritative
- handoff bundles are derived and read-only from this repository's perspective
- local evaluation artifacts are downstream review support, not Chronicle-side
  evidence on their own

The remaining architectural decision is whether this repository should gain any
direct Chronicle mutation path for trial persistence, review status updates, or
downstream write-back.

## Decision

Chronicle write-back remains explicitly out of scope for
`chronicle-external-query`.

This repository will not:

- write local evaluation artifacts into Chronicle primary records
- assign Chronicle-side event ids
- mark Chronicle-side trial review completion
- persist hosted-provider comparison output back into Chronicle
- blur downstream review support into Chronicle-authoritative state

If future work ever requires Chronicle mutation, that work must be accepted as
a separate architectural change in a different milestone, with an explicit
contract, authority model, and persistence design.

## Consequences

### Positive

- keeps Chronicle authority boundaries clear
- prevents accidental mutation through plugin loading or release automation
- preserves a simple mental model: this repo consumes bundles and emits
  downstream review artifacts only
- allows local and hosted experimentation without turning comparison output into
  authoritative Chronicle state

### Negative

- operators who want Chronicle-side persistence must use another system or a
  future explicitly approved bridge
- no automatic Chronicle-side audit trail is created from local runtime work

## Operational Rule

When evaluating a proposed enhancement, reject it from this repository if it
would:

- write back into Chronicle storage
- change Chronicle-side review state
- persist downstream-derived judgments as authoritative Chronicle facts

Such work belongs either outside this repository or behind a future ADR that
reopens this boundary deliberately.
