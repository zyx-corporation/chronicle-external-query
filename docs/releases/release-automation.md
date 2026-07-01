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

Run the current-checkout operator preflight locally:

```bash
bash scripts/operator_preflight.sh
```

Run the same gate with optional plugin checks enabled:

```bash
RUN_OPTIONAL_PLUGIN_MATRIX=1 bash scripts/release_candidate_gate.sh
```

Run GitHub Actions locally with `act`:

```bash
bash scripts/run_local_act.sh doctor
bash scripts/run_local_act.sh ci
bash scripts/run_local_act.sh all
bash scripts/run_local_act.sh release-verify
bash scripts/run_local_act.sh release-verify-optional
bash scripts/run_local_act.sh release-notes
ACT_ARGS="--pull=false" bash scripts/run_local_act.sh ci -- --verbose
```

Notes:

- repository-local `.actrc` pins the runner image mapping and avoids the first-run prompt
- default `workflow_dispatch` inputs live in `.github/act/release-dispatch.event.json`
- optional-plugin rehearsal inputs live in `.github/act/release-dispatch.optional-plugins.event.json`
- set `ACT_EVENT_FILE=/path/to/event.json` to test alternate release inputs
- set `ACT_OPTIONAL_EVENT_FILE=/path/to/event.json` to override only the optional-plugin rehearsal inputs
- `doctor` checks `act`, Docker, the Docker Desktop credential helper, and the event payload path before a rehearsal run
- `operator_preflight.sh` is the fastest same-checkout confirmation path before a release-candidate gate run
- `all` runs the local CI baseline and then the release workflow through `build-release-notes`, letting the workflow dependency chain cover `verify` once
- `release-verify-optional` runs the same local release gate with `run_optional_plugin_matrix=true`
- `ACT_ARGS` and trailing `-- ...` let operators pass through extra `act` flags for local debugging or cache-control runs
- local `act` skips artifact upload/download steps because they depend on
  GitHub-hosted runtime tokens
- local rehearsal covers `release-verify` and `release-notes`; real GitHub
  release publication still runs on tag push or hosted workflow dispatch

## Boundary Rules

- optional plugin failures do not block the baseline release by default
- optional plugin compatibility is reported separately from the baseline smoke
- plugin-backed release evidence must not be presented as Chronicle-authoritative
- hosted or local provider credentials remain isolated to plugin-specific
  environment variables
