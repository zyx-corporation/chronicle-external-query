# Query-Engine Bundle Contract Notes

This note captures the current Chronicle-side contract details that
`chronicle-external-query` validates against during Milestone A.

## Source

These notes are derived from Chronicle Stack's local downstream handoff bundle
behavior and related ADRs for:

- downstream query-engine handoff
- import-validation preview
- local handoff bundle generation

## Supported Versions

- bundle manifest contract version: `1.0`
- handoff contract version: `1.0`
- graph export contract version: `1.0`
- adapter skeleton contract version: `1.0`
- graph export format / family: `graph-json`

## Required Bundle Files

Core bundle files currently expected:

- `bundle_manifest.json`
- `query_engine_handoff.json`
- `query_engine_adapter_skeleton.json`
- `graph.json`
- `ACCEPTANCE_CHECKLIST.md`
- `TRIAL_REPORT_TEMPLATE.md`

## Observed Boundary Notes

- the bundle is descriptive and read-only
- Chronicle primary records remain authoritative
- import validation is structural only and does not execute downstream runtime
- the bundle may point at `.chronicle/chronicle.jsonl` via metadata without
  embedding the primary record inside the bundle directory
