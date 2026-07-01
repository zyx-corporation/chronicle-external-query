# chronicle-external-query

`chronicle-external-query` is a downstream runtime workspace for
Chronicle-derived handoff bundles.

It exists to solve a specific boundary problem in Chronicle Stack.
Chronicle Stack can produce useful derived outputs for downstream query engines
such as `query_engine_handoff.json`, `graph.json`, `bundle_manifest.json`, and
a descriptive import-adapter skeleton, but Chronicle itself should not become
the place where external query execution, hosted retrieval infrastructure,
provider experimentation, or downstream runtime behavior quietly accumulates.

This repository is the separate implementation surface for that next step.
It receives Chronicle-generated bundle outputs, validates them as contracts,
loads them as read-only downstream inputs, runs retrieval and local runtime
evaluation on top of them, and produces repeatable review artifacts such as
saved evaluation JSON and markdown reports.

That separation is necessary because the concerns are different:

- Chronicle Stack is the authoritative producer of primary records and derived handoff bundles
- `chronicle-external-query` is the downstream consumer that tests whether those bundles are sufficient for real query-engine use
- Chronicle should preserve source authority and boundary discipline
- this repository can evolve retrieval logic, runtime behavior, and comparison tooling without weakening Chronicle's role as the system of record

In practice, this means the repository is the place to answer questions like:

- can a Chronicle handoff bundle be validated safely before downstream use?
- does graph-only or hybrid retrieval preserve enough provenance to be reviewable?
- can local runtime answers be compared across repeated runs?
- can a downstream consumer evaluate bundle sufficiency without asking Chronicle core to become an execution runtime?

The repository is intentionally boundary-conscious:

- it treats Chronicle primary records as authoritative
- it keeps ingest, retrieval, runtime, and evaluation concerns explicit
- it supports local-only deterministic validation paths first
- it avoids implicit write-back into Chronicle core
- it leaves hosted provider integrations and other future extensions outside the
  default baseline until they can be added through clear plugin seams

Japanese README: [README.ja.md](README.ja.md)

## Boundary

- Chronicle `.chronicle/chronicle.jsonl` remains authoritative
- this repository consumes derived exports and handoff contracts
- no writes back to Chronicle are performed implicitly
- graph/vector/query runtime concerns live here, not in Chronicle core

## Current Scope

This repository currently provides:

- loading for real Chronicle handoff bundle directories
- contract-version, required-file, and required-key validation
- graph export loading
- adapter skeleton loading
- sanitized real-bundle fixtures for contract tests
- graph-only and hybrid retrieval result scaffolding with shared provenance,
  overlap tracking, and provider-neutral vector seams
- a pluggable fixture registry with committed baseline fixtures and optional
  manifest-driven fixture packs
- an explicit provider plugin registry with env-only credential discovery and
  opt-in provider test isolation
- a local `gemma4` answer plugin that stays opt-in and preserves the baseline
  runtime path when not requested
- an optional hosted provider plugin plus comparative evaluation against the
  deterministic baseline

## Repository Layout

```text
chronicle-external-query/
  docs/
  contracts/
    chronicle/
  src/chronicle_external_query/
    ingest/
    retrieval/
    runtime/
    evaluation/
  tests/
```

## Documentation

- [Architecture](docs/architecture.md)
- [Roadmap](docs/roadmap.md)
- [Extension Roadmap](docs/extension-roadmap.md)
- [Pluggable Extension Spec](docs/pluggable-extension-spec.md)
- [Coding Guidelines](docs/coding-guidelines.md)
- [Development Workflow](docs/development-workflow.md)
- [Testing Strategy](docs/testing-strategy.md)
- [Retrieval Contract](docs/retrieval-contract.md)
- [Runtime Answer Contract](docs/runtime-answer-contract.md)
- [Chronicle Trial Alignment](docs/chronicle-trial-alignment.md)
- [Chronicle Write-back Boundary](docs/chronicle-writeback-boundary.md)
- [Clean Checkout](docs/clean-checkout.md)
- [Operator Runbook](docs/operator-runbook.md)
- [Release Automation](docs/releases/release-automation.md)
- [i18n Strategy](docs/i18n-strategy.md)
- [ADR Index](docs/adr/README.md)

## Local Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

One-command baseline smoke:

```bash
bash scripts/smoke_clean_checkout.sh
```

Current-checkout operator preflight:

```bash
bash scripts/operator_preflight.sh
```

If your default `python3` is older than 3.11, set `PYTHON_BIN` explicitly, for
example `PYTHON_BIN=/usr/local/bin/python3.11 bash scripts/smoke_clean_checkout.sh`.

## Local CLI

```bash
chronicle-external-query validate-bundle /path/to/handoff-bundle --json
chronicle-external-query show-bundle /path/to/handoff-bundle --json
chronicle-external-query list-fixtures --json
chronicle-external-query list-plugins --json
chronicle-external-query doctor-plugin gemma4 --json
chronicle-external-query run-query /path/to/handoff-bundle --query "release planning context" --mode graph --answer-plugin gemma4 --json
chronicle-external-query compare-query-runs /path/to/handoff-bundle --query "release planning context" --mode graph --answer-plugin openai-compatible-hosted --json
chronicle-external-query run-query /path/to/handoff-bundle --query "release planning context" --mode graph --json
chronicle-external-query render-artifact-report trial-artifact.json --output trial-report.md --json
chronicle-external-query render-comparison-report first-artifact.json second-artifact.json --output comparison-report.md --json
```

Local plugin bootstrap:

```bash
bash scripts/bootstrap_plugin_env.sh
source .env.local.plugins
chronicle-external-query doctor-plugin gemma4 --json
```

## Fixture Registry

Milestone F adds a pluggable fixture registry without changing the supported
baseline path.

- `baseline_minimal` and `baseline_representative` remain committed in-repo
  fixtures and still back the default test suite
- optional fixture packs can be added through `fixture-pack.json` manifests
- optional fixture pack directories can be passed with `--fixture-dir` or
  discovered from `CHRONICLE_EXTERNAL_QUERY_FIXTURE_DIRS`

Example:

```bash
chronicle-external-query list-fixtures --json --no-env-fixture-dirs
CHRONICLE_EXTERNAL_QUERY_FIXTURE_DIRS=/path/to/fixture-pack chronicle-external-query list-fixtures --json
```

Manifest shape:

```json
{
  "manifest_version": "1.0",
  "source_name": "comparison_pack",
  "fixtures": [
    {
      "fixture_id": "provider_comparison_bundle",
      "fixture_kind": "optional_provider_comparison_pack",
      "bundle_dir": "bundles/provider_comparison_bundle",
      "vector_fixture": "vectors/provider_comparison_matches.json",
      "metadata": {
        "origin": "sanitized Chronicle-derived fixture pack",
        "sanitization_status": "sanitized",
        "intended_test_scope": ["provider_comparison"]
      }
    }
  ]
}
```

## Provider Plugin Surface

Milestone G adds the provider plugin seam without making any provider
mandatory.

- provider plugins are registered explicitly and inspected through
  `chronicle-external-query list-plugins --json`
- per-plugin readiness can be inspected through
  `chronicle-external-query doctor-plugin <plugin-name> --json`
- credentials stay isolated to plugin-specific environment variables
- the default `pytest` and smoke baseline do not run provider plugin tests
- provider availability is reported explicitly instead of mutating the baseline
  path silently

Current built-in provider seam:

- `static-test-provider`
- required credential env var:
  `CHRONICLE_EXTERNAL_QUERY_STATIC_TEST_PROVIDER_API_KEY`
- optional endpoint override:
  `CHRONICLE_EXTERNAL_QUERY_STATIC_TEST_PROVIDER_ENDPOINT`
- runtime integration remains reserved-only

Opt-in provider tests:

```bash
pytest --run-provider-plugins tests/providers/
```

Provider readiness examples:

```bash
chronicle-external-query doctor-plugin static-test-provider --json
chronicle-external-query doctor-plugin gemma4 --json
chronicle-external-query doctor-plugin openai-compatible-hosted --json
```

## Local Gemma4 Plugin

Milestone H adds the first real answer-generation plugin while keeping the
deterministic runtime as the default.

- plugin name: `gemma4`
- CLI activation: `--answer-plugin gemma4`
- local runtime expectation: OpenAI-compatible `POST /v1/chat/completions`
- default path: unchanged when `--answer-plugin` is omitted
- failure mode: explicit plugin error when requested but not configured or not
  reachable

Required environment:

- `GEMMA4_ENABLED=true`
- `GEMMA4_BASE_URL=http://127.0.0.1:11434`
- `GEMMA4_MODEL=gemma4`

Optional environment:

- `GEMMA4_TIMEOUT=30`
- `GEMMA4_API_KEY=...`

Example:

```bash
bash scripts/bootstrap_plugin_env.sh
source .env.local.plugins
chronicle-external-query run-query tests/fixtures/query_engine_bundle/representative_cli_bundle --query "release planning follow-up context" --mode hybrid --vector-fixture tests/fixtures/vector_matches/representative-vector-matches.json --answer-plugin gemma4 --json
```

Opt-in gemma4 tests:

```bash
pytest --run-provider-plugins --run-gemma4 tests/providers/test_gemma4_plugin.py
```

## Hosted Provider Comparison

Milestone I adds the first hosted provider plugin and a one-shot comparative
evaluation flow.

- hosted plugin name: `openai-compatible-hosted`
- comparison CLI:
  `chronicle-external-query compare-query-runs ... --answer-plugin openai-compatible-hosted`
- baseline smoke path: unchanged
- comparison contract: reuses the same evaluation artifact shape and standard
  artifact comparison fields

Required environment:

- `OPENAI_COMPATIBLE_HOSTED_ENABLED=true`
- `OPENAI_COMPATIBLE_HOSTED_BASE_URL=https://api.openai.com`
- `OPENAI_COMPATIBLE_HOSTED_MODEL=gpt-5.4`
- `OPENAI_COMPATIBLE_HOSTED_API_KEY=...`

Recommended local staging path:

- `bash scripts/bootstrap_plugin_env.sh`
- `source .env.local.plugins`
- set `OPENAI_COMPATIBLE_HOSTED_ENABLED=true`
- fill `OPENAI_COMPATIBLE_HOSTED_MODEL`
- fill `OPENAI_COMPATIBLE_HOSTED_API_KEY`
- keep `OPENAI_COMPATIBLE_HOSTED_BASE_URL=https://api.openai.com` for the default OpenAI hosted path, or replace it with another OpenAI-compatible provider base URL

Optional environment:

- `OPENAI_COMPATIBLE_HOSTED_TIMEOUT=30`

Example:

```bash
source .env.local.plugins
OPENAI_COMPATIBLE_HOSTED_ENABLED=true \
OPENAI_COMPATIBLE_HOSTED_BASE_URL=https://api.openai.com \
OPENAI_COMPATIBLE_HOSTED_MODEL=gpt-5.4 \
OPENAI_COMPATIBLE_HOSTED_API_KEY=secret \
chronicle-external-query compare-query-runs tests/fixtures/query_engine_bundle/representative_cli_bundle --query "release planning follow-up context" --mode hybrid --vector-fixture tests/fixtures/vector_matches/representative-vector-matches.json --answer-plugin openai-compatible-hosted --baseline-output baseline-artifact.json --plugin-output hosted-artifact.json --json
```

Opt-in hosted-provider tests:

```bash
pytest --run-provider-plugins --run-hosted-providers tests/providers/test_openai_compatible_hosted_plugin.py
```

## CI Baseline

```bash
bash scripts/smoke_clean_checkout.sh
```

The same baseline runs in GitHub Actions on pushes and pull requests to `main`.

Local `act` execution:

```bash
bash scripts/run_local_act.sh doctor
bash scripts/run_local_act.sh ci
bash scripts/run_local_act.sh all
ACT_ARGS="--pull=false" bash scripts/run_local_act.sh ci -- --verbose
```

This repository includes a checked-in `.actrc` so `act` can run non-interactively
with the `ubuntu-latest` runner mapping already selected.

## Release Automation

Milestone J adds release automation beyond the baseline CI path.

- release workflow: `.github/workflows/release.yml`
- release-candidate gate: `bash scripts/release_candidate_gate.sh`
- release notes generator: `python scripts/generate_release_notes.py --version vX.Y.Z`
- plugin compatibility report: `python scripts/check_plugin_compatibility.py`

Optional plugin checks remain non-blocking for the baseline release unless they
are explicitly required by the release operator.

Local `act` release verification:

```bash
bash scripts/run_local_act.sh release-verify
bash scripts/run_local_act.sh release-verify-optional
bash scripts/run_local_act.sh release-notes
```

The default workflow-dispatch payload lives at
`.github/act/release-dispatch.event.json`. Override it with `ACT_EVENT_FILE=...`
when you want to test a different local release input set.
For the optional-plugin path, use `ACT_OPTIONAL_EVENT_FILE=...` when you want
to swap only the optional matrix rehearsal inputs.

Use `release-verify-optional` when you want the local release gate to exercise
the optional plugin matrix without editing the default event payload.

Use `doctor` first if `act` cannot find Docker or its credential helper. Use
`all` when you want the full local rehearsal in one command. It runs the CI
baseline plus the release workflow up through `build-release-notes`, so the
release gate is covered once through the workflow dependency chain.
Use `ACT_ARGS` or `-- ...` when you want to forward extra `act` flags without
editing the script.

Under local `act`, artifact upload/download and GitHub release publication stay
disabled. Use `release-verify` for the gate, `release-notes` for the notes job,
then let GitHub run the publish path on tag push or hosted workflow dispatch.

## Release Status

The current release-preparation target is `v0.3.0`.

Release-closeout artifacts:

- [v0.3.0 Release Notes](docs/releases/v0.3.0-release-notes.md)
- [v0.3.0 Completion Checklist](docs/releases/v0.3.0-completion-checklist.md)
- [v0.3.0 Boundary Summary](docs/releases/v0.3.0-boundary-summary.md)
- [v0.3.0 Chronicle Stack Handoff](docs/releases/v0.3.0-chronicle-stack-handoff.md)

The original first supported local downstream runtime baseline remains
documented in
[docs/releases/v0.2.0-first-supported-baseline.md](docs/releases/v0.2.0-first-supported-baseline.md).

The post-`v0.2.0` extension track now has Milestone F implemented locally:
fixture growth is registry-driven, while the default smoke and `pytest` path
remain pinned to committed baseline fixtures.

Milestone G is also implemented locally: provider plugin registration,
credential isolation, and opt-in provider test gating are now in place without
changing the supported baseline runtime path.

Milestone H is now implemented locally as well: `gemma4` can be requested as a
local answer plugin, while the supported baseline remains deterministic and
provider-free by default.

Milestone I is now implemented locally too: hosted provider plugins remain
optional, and comparative evaluation can be run without changing the baseline
artifact contract.

Milestone J is now implemented locally as well: release notes, RC gating,
plugin-compatibility reporting, and tag/manual GitHub release automation are in
place without changing the supported baseline release boundary.

Milestone K is now implemented too: Chronicle write-back remains explicitly out
of scope, so the roadmap is complete without introducing any accidental
Chronicle mutation path.

That means the repository is now prepared for a `v0.3.0` release on the
current supported boundary.
