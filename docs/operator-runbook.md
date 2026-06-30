# Operator Runbook

This runbook covers the current local-only validation and query workflow for
`chronicle-external-query`.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Repository CI baseline:

```bash
bash scripts/smoke_clean_checkout.sh
```

GitHub Actions also runs the same baseline on pushes and pull requests to
`main`.

For a shortest-path fresh clone workflow, see [Clean Checkout](clean-checkout.md).

What the baseline smoke covers:

- editable install from the current checkout
- full `pytest`
- minimal bundle validation and inspection
- representative hybrid query using only checked-in local fixtures
- markdown trial and comparison report rendering

If the machine's default `python3` is older than 3.11, set `PYTHON_BIN`
explicitly before running the smoke script.

## Validate a Bundle

```bash
chronicle-external-query validate-bundle /path/to/handoff-bundle --json
```

If the installed script is not yet on your shell `PATH`, use:

```bash
python -m chronicle_external_query.cli validate-bundle /path/to/handoff-bundle --json
```

What this does:

- loads the bundle
- validates required files and key contract versions
- checks core contract consistency across manifest, handoff, graph, and adapter
  skeleton payloads

## Inspect a Bundle

```bash
chronicle-external-query show-bundle /path/to/handoff-bundle --json
```

What this does:

- loads the bundle through the same validation path
- reports bundle kind and supported contract versions
- shows primary-record availability plus graph node and edge counts

## Run a Local Query

```bash
chronicle-external-query run-query /path/to/handoff-bundle --query "release planning context" --mode graph --json
```

PATH fallback:

```bash
python -m chronicle_external_query.cli run-query /path/to/handoff-bundle --query "release planning context" --mode graph --json
```

Optional artifact output:

```bash
chronicle-external-query run-query /path/to/handoff-bundle --query "release planning context" --mode hybrid --output trial-artifact.json --json
```

Optional local vector fixture for hybrid evaluation:

```bash
chronicle-external-query run-query /path/to/handoff-bundle --query "release planning context" --mode hybrid --vector-fixture /path/to/vector-matches.json --json
```

Optional fixture pack discovery:

```bash
chronicle-external-query list-fixtures --json --no-env-fixture-dirs
CHRONICLE_EXTERNAL_QUERY_FIXTURE_DIRS=/path/to/fixture-pack chronicle-external-query list-fixtures --json
```

Each optional fixture pack directory must contain `fixture-pack.json`. This is
an extension surface for extra regression packs and provider-comparison suites;
the baseline smoke path continues to rely only on the committed in-repo
fixtures.

Optional provider plugin inspection:

```bash
chronicle-external-query list-plugins --json
```

Current provider plugin boundary rules:

- provider plugins are advisory and opt-in
- missing credentials must produce an unavailable state, not a baseline failure
- provider runtime behavior must not become the default answer path before an
  explicit follow-on milestone
- plugin credentials stay in plugin-specific environment variables instead of
  shared baseline configuration

Opt-in local gemma4 answer generation:

```bash
GEMMA4_ENABLED=true \
GEMMA4_BASE_URL=http://127.0.0.1:11434 \
GEMMA4_MODEL=gemma4 \
chronicle-external-query run-query /path/to/handoff-bundle --query "release planning context" --mode graph --answer-plugin gemma4 --json
```

Operational expectations:

- the local runtime must expose an OpenAI-compatible `POST /v1/chat/completions`
- if `--answer-plugin gemma4` is requested without valid config, the command
  must fail explicitly
- if `gemma4` is not requested, the deterministic baseline answer path remains
  unchanged

## Review a Saved Artifact

```bash
chronicle-external-query show-artifact trial-artifact.json --json
```

This returns compact provenance counts alongside the saved artifact fields.

## Compare Two Saved Artifacts

```bash
chronicle-external-query compare-artifacts first-artifact.json second-artifact.json --json
```

This returns both the full comparison payload and a compact summary with changed
field names and a difference count.

## Render a Markdown Trial Report

```bash
chronicle-external-query render-artifact-report trial-artifact.json --output trial-report.md --json
```

This returns both the markdown body and a small JSON summary including runtime
status, retrieval mode, match count, and markdown line count.

## Render a Markdown Comparison Report

```bash
chronicle-external-query render-comparison-report first-artifact.json second-artifact.json --output comparison-report.md --json
```

This returns both the markdown body and a compact comparison summary so
automation can inspect major deltas without reparsing markdown.

## Current Boundaries

- local-only execution
- no Chronicle write-back
- no hosted vector provider required for the default path
- hybrid mode currently uses a provider-neutral null vector fallback unless a
  different adapter is wired in code or supplied through `--vector-fixture`

## Failure Modes

- missing required bundle files
- malformed JSON
- unsupported contract versions
- bundle payload mismatches across manifest, handoff, graph, and adapter
- invalid local vector fixture shape or missing required vector fixture fields
- invalid evaluation artifact JSON or missing required evaluation artifact fields

These artifact-validation failures are surfaced consistently across
`show-artifact`, `compare-artifacts`, `render-artifact-report`, and
`render-comparison-report`.

Machine-readable JSON failures also include `error_code` and `error_category`.
Current codes:

- `bundle_validation.missing_required_file`
- `bundle_validation.invalid_json`
- `bundle_validation.invalid_bundle_object`
- `bundle_validation.missing_required_key`
- `bundle_validation.unsupported_contract_version`
- `bundle_validation.contract_consistency`
- `vector_fixture_validation.invalid_fixture`
- `evaluation_artifact_validation.invalid_artifact`

These failures are validation failures, not partial success.
