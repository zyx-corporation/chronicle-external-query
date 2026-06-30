# Representative CLI Bundle Fixture

This fixture was generated from a real Chronicle Stack CLI flow and then
sanitized for deterministic in-repo testing.

## Generation Source

The source Chronicle project was created with:

```bash
chronicle init --title "Milestone A Fixture"
chronicle add-context --title "Release Planning" --summary "Representative release planning notes for downstream query-engine bundle validation."
chronicle add-context --title "Incident Follow-up" --summary "Operational follow-up context to ensure multiple graph nodes are present."
chronicle package query-engine-bundle --query "release planning follow-up context" --output-dir handoff-bundle
```

## Sanitization

- unstable record ids were replaced with stable fixture ids
- timestamps were normalized to deterministic values
- graph export generation metadata was normalized
- the copied `.chronicle/chronicle.jsonl` file was sanitized to exercise the
  optional primary-record ingest path

## Notes

- raw Chronicle bundle output does not embed `.chronicle/chronicle.jsonl`
- this fixture includes a sanitized primary record copy on purpose so
  `HandoffLoader` contract tests can cover the optional local primary-record
  read path using representative data
- this fixture is intended for Milestone A ingest and contract validation, not
  retrieval quality benchmarking
