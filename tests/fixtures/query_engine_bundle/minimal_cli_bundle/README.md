# Minimal CLI Bundle Fixture

This fixture was generated from a real Chronicle Stack CLI flow:

```bash
python3 -m chronicle.cli init --title "Fixture Bundle"
python3 -m chronicle.cli package query-engine-bundle --query "fixture query" --output-dir bundle
```

The source Chronicle project was intentionally minimal so the fixture stays
small while still reflecting real downstream bundle structure.

## Notes

- this fixture captures the bundle directory only
- the bundle metadata still points at `.chronicle/chronicle.jsonl`
- the primary record is not embedded in the bundle directory
- the fixture is intended for ingest and contract validation tests
