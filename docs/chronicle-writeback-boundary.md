# Chronicle Write-back Boundary

This document records the final Milestone K boundary review for
`chronicle-external-query`.

## Decision

Chronicle write-back remains out of scope.

This repository may:

- read Chronicle-derived handoff bundles
- inspect the optional primary record path referenced by bundle metadata
- produce downstream evaluation artifacts, markdown reports, and comparison
  outputs
- automate release packaging for this downstream runtime workspace

This repository may not:

- mutate Chronicle primary records
- write downstream trial artifacts back into Chronicle
- publish provider-backed answer output as Chronicle-authoritative state
- mark Chronicle-side review completion

## Why

The repository now includes optional fixture packs, optional provider plugins,
comparative evaluation, and release automation. Those features increase the
amount of useful downstream review material, but they do not change authority.

Chronicle remains the system of record.
`chronicle-external-query` remains a downstream consumer and evaluator.

## Practical Interpretation

- local JSON artifacts are downstream review support
- plugin-backed answers are downstream review support
- markdown reports are downstream review support
- release automation is packaging and publication support for this repository
- none of the above become Chronicle evidence automatically

## Escalation Rule

If a future feature needs Chronicle mutation, stop treating it as an ordinary
plugin or runtime enhancement. It must first pass through an explicit
architecture review that defines:

- what is being written
- who owns authority over that data
- how Chronicle-side identifiers are assigned
- how non-authoritative downstream judgments avoid masquerading as Chronicle
  facts

Until then, no write-back path belongs in this repository.
