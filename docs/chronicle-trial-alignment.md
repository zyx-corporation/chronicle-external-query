# Chronicle Trial Alignment

This document explains how local evaluation artifacts in
`chronicle-external-query` align with Chronicle-side downstream trial review
expectations.

## Purpose

Chronicle Stack already defines a structured downstream trial review flow around:

- bundle sufficiency
- missing behavior
- downstream consumer identity
- reviewer identity
- files reviewed

This repository should produce local artifacts that can map into that review
shape without implying that Chronicle has accepted, adopted, or certified the
result.

## Local-to-Chronicle Mapping

Local evaluation artifacts currently map as follows:

- `query` -> Chronicle trial `query`
- `reviewer` -> Chronicle trial `reviewer`
- `downstream_consumer` -> Chronicle trial `downstream_consumer`
- `sufficient` -> Chronicle trial `sufficient`
- `missing_behavior` -> Chronicle trial `missing_behavior`
- `files_reviewed` -> Chronicle trial `files_reviewed`
- `bundle_summary` -> local-only bundle identity and graph-size context for trial review
- runtime metadata status -> local approximation of `import_validation_status`
- runtime metadata retrieval mode and top matches remain local-only review support

## Boundary Rules

- the local artifact remains downstream-derived
- the local artifact does not mutate Chronicle primary records
- the local artifact does not imply Chronicle-side review completion
- the local artifact should preserve insufficiency and missing behavior rather
  than collapsing them into a success-looking summary
- markdown trial reports should keep bundle contract versions and retrieval
  provenance visible so reviewers do not need to reopen raw JSON first
- markdown comparison reports should keep left/right provenance and
  insufficiency visible so reviewers can compare runs without reopening raw
  JSON first

## Current Gaps

- no direct Chronicle write-back is performed here
- no event id is assigned from Chronicle core
- local comparison artifacts are still review support, not Chronicle evidence on
  their own

## Final Boundary Review

Milestone K closes this gap intentionally rather than extending it.

- Chronicle write-back remains out of scope for this repository
- local artifacts stay downstream-derived even when plugin-backed or
  release-automation-assisted
- any future Chronicle mutation would require a separate architectural decision

See [Chronicle Write-back Boundary](chronicle-writeback-boundary.md) and
[ADR-003](adr/ADR-003-chronicle-writeback-remains-out-of-scope.md).
