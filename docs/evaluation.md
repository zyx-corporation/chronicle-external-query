# Evaluation

Evaluation should begin from real Chronicle-generated bundles and keep
provenance visible.

## Initial Loop

1. Load a bundle directory with `HandoffLoader`.
2. Validate required files before retrieval starts.
3. Run retrieval against a query.
4. Build a runtime answer with explicit status and provenance.
5. Serialize a local evaluation artifact for review or comparison, including
   bundle identity and graph-size summary fields.
6. Reject malformed JSON, invalid object shapes, or partial artifact files before review or comparison
   continues.

## Expansion Path

- compare graph-only vs hybrid retrieval
- record repeated insufficiency patterns
- surface missing behavior before adding more runtime complexity
- compare serialized artifacts across repeated runs
- keep bundle summary fields stable enough to compare runs across bundle exports
- treat bundle identity, contract-version changes, and graph-size drift as
  first-class comparison outputs, not just answer deltas
- render markdown comparison reports when human review is more useful than raw
  JSON comparison output
- keep left/right provenance and insufficiency summaries visible in comparison
  reports so review does not depend on reopening artifact JSON
