# Query-Engine Handoff Bundle Acceptance Checklist

- Query: `release planning follow-up context`
- [ ] `query_engine_handoff.json` is present and parses successfully
- [ ] `query_engine_adapter_skeleton.json` is present and remains descriptive only
- [ ] `graph.json` is present and matches the expected `graph-json` contract version
- [ ] `bundle_manifest.json` is present and lists every emitted file
- [ ] `import_validation.status` is reviewed as a structural signal only
- [ ] no consumer treats derived bundle files as authoritative over `.chronicle/chronicle.jsonl`
- [ ] no consumer assumes hosted query execution, graph runtime, or vector runtime inside Chronicle Stack
- [ ] a downstream implementation repo is requested only if this bundle is insufficient

Boundary:
- local read-only bundle only
- no downstream import execution inside Chronicle Stack
- no mutation of `.chronicle/chronicle.jsonl`