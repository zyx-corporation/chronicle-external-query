# Query-Engine Bundle Contract Source Map

This map traces `chronicle-external-query` ingest validation back to the current
Chronicle Stack contract sources.

## Upstream Sources

- `chronicle-stack/docs/downstream-query-engine-handoff-bundle.md`
  Purpose: defines bundle contents, intended use, and boundary wording.
- `chronicle-stack/docs/examples/query-engine-handoff-example.json`
  Purpose: documents the handoff payload shape and import-validation fields.
- `chronicle-stack/docs/examples/query-engine-import-adapter-skeleton.json`
  Purpose: documents the adapter skeleton payload shape.
- `chronicle-stack/src/chronicle/cli_package.py`
  Purpose: current bundle writer for `query-engine-bundle`, including
  `ACCEPTANCE_CHECKLIST.md` and `TRIAL_REPORT_TEMPLATE.md`.
- `chronicle-stack/src/chronicle/services/integration_package_service.py`
  Purpose: current manifest construction and bundle file list.
- `chronicle-stack/src/chronicle/services/runtime_service.py`
  Purpose: current `query_engine_handoff.json` field population and
  import-validation contract.
- `chronicle-stack/src/chronicle/services/graph_export_service.py`
  Purpose: current `graph.json` export contract and graph-export metadata.

## Validation Rule Mapping

- Required files:
  `bundle_manifest.json`, `query_engine_handoff.json`,
  `query_engine_adapter_skeleton.json`, `graph.json`,
  `ACCEPTANCE_CHECKLIST.md`, and `TRIAL_REPORT_TEMPLATE.md` come from the
  Chronicle bundle documentation and current bundle writer implementation.
- `bundle_manifest.json` contract:
  validated fields track the current manifest emitted by Chronicle's
  integration-package service and CLI package command.
- `query_engine_handoff.json` contract:
  validated fields track the documented handoff example and the runtime-service
  handoff builder, including `import_validation`.
- `query_engine_adapter_skeleton.json` contract:
  validated fields track the documented adapter example and the current
  adapter-skeleton builder.
- `graph.json` contract:
  validated fields track the graph export contract emitted by Chronicle's
  graph-export service.
- Cross-file consistency checks:
  version and format matching mirror the Chronicle-side relationship between
  manifest, handoff, adapter skeleton, and graph export payloads.

## Vendored vs Referenced

- Vendored here:
  concise downstream notes and this traceability map.
- Referenced upstream:
  the fuller Chronicle examples and implementation sources listed above.

The goal is to keep local ingest validation traceable without copying large
upstream payloads unnecessarily.
