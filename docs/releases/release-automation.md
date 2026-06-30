# Release Automation

This document records the Milestone J release automation path for
`chronicle-external-query`.

## Goals

- keep `bash scripts/smoke_clean_checkout.sh` as the primary release gate
- make plugin compatibility visible without forcing optional plugins into the
  baseline release
- generate release notes from repository-resident release and roadmap context
- allow tag-driven or manually dispatched GitHub releases

## Release Workflow

GitHub workflow:

- `.github/workflows/release.yml`

Trigger modes:

- push a tag like `v0.3.0`
- manually dispatch the workflow with:
  - `version`
  - `publish_release`
  - `run_optional_plugin_matrix`

Jobs:

1. `verify`
   - runs `bash scripts/release_candidate_gate.sh`
   - uploads `plugin-compatibility-report`
2. `build-release-notes`
   - runs `scripts/generate_release_notes.py`
   - uploads `release-notes`
3. `publish-release`
   - creates or updates a GitHub release with generated notes

## Local Release Helpers

Generate release notes locally:

```bash
PYTHONPATH=src python scripts/generate_release_notes.py --version v0.3.0-rc1
```

Check plugin compatibility locally:

```bash
PYTHONPATH=src python scripts/check_plugin_compatibility.py
```

Run the release-candidate gate locally:

```bash
bash scripts/release_candidate_gate.sh
```

Run the same gate with optional plugin checks enabled:

```bash
RUN_OPTIONAL_PLUGIN_MATRIX=1 bash scripts/release_candidate_gate.sh
```

## Boundary Rules

- optional plugin failures do not block the baseline release by default
- optional plugin compatibility is reported separately from the baseline smoke
- plugin-backed release evidence must not be presented as Chronicle-authoritative
- hosted or local provider credentials remain isolated to plugin-specific
  environment variables
