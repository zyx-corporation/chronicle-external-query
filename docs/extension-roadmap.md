# Extension Roadmap

This roadmap defines the post-`v0.2.0` expansion track for
`chronicle-external-query`.

The guiding decision is to keep the `v0.2.0` baseline deterministic,
local-first, and provider-neutral while making future fixture expansion and
provider-backed evaluation pluggable rather than hardwired into the core path.

## Guiding Rule

- keep the current `v0.2.0` smoke path valid without any external provider
- add future fixture sources and provider-backed tests through extension points
- keep Chronicle primary records authoritative and unchanged
- isolate credentials, provider SDKs, and hosted runtime assumptions outside the
  default baseline

## Current Starting Point

`v0.2.0` already provides:

- deterministic minimal and representative fixture bundles
- provider-neutral retrieval seams
- local-only runtime answers and evaluation artifacts
- reproducible smoke validation from a clean checkout

That means the next work is not to replace the baseline, but to extend it
through plugins.

## Milestone F: Pluggable Fixture Registry

Status:
Completed on 2026-06-30.

Goal:
Turn fixture expansion into a registry-driven extension surface instead of
growing one fixed in-repo fixture tree.

Scope:

- define a fixture-source protocol and fixture manifest shape
- separate baseline fixtures from optional fixture suites
- allow opt-in fixture packs to be discovered without changing core ingest code
- keep deterministic baseline fixture coverage intact

Exit Criteria:

- the core test suite still runs from committed baseline fixtures only
- optional fixture packs can be added through a registry/config surface
- fixture metadata explains origin, sanitization, and intended use

Delivered:

- `chronicle_external_query.fixtures` now provides `FixtureRegistry`,
  `FixtureSet`, and a fixture-source protocol
- committed baseline fixtures are registered as `baseline_minimal` and
  `baseline_representative`
- optional fixture packs can be loaded from `fixture-pack.json` through
  `--fixture-dir` or `CHRONICLE_EXTERNAL_QUERY_FIXTURE_DIRS`
- `list-fixtures` exposes the resolved registry as a local inspection surface

## Milestone G: Provider Plugin Surface and Credential Isolation

Status:
Completed on 2026-06-30.

Goal:
Make provider-backed tests and runtime adapters pluggable, opt-in, and isolated
from the default local-only baseline.

Scope:

- define plugin interfaces for provider-backed runtime or evaluation adapters
- isolate provider configuration and credentials from the default test path
- add explicit opt-in test markers or entrypoints for provider plugins
- document boundary rules for plugin loading and failure behavior

Exit Criteria:

- provider-backed tests do not run in the default `pytest` or smoke path
- credential handling is isolated to plugin configuration
- the core package can operate without any provider plugin installed

Delivered:

- `chronicle_external_query.plugins` now provides provider plugin contracts,
  registry definitions, and explicit loader behavior
- `list-plugins` exposes plugin availability, configuration fields, and
  credential isolation metadata
- provider credentials are isolated to plugin-specific environment variables
- provider tests are gated behind `--run-provider-plugins` and
  `--run-hosted-providers`

## Milestone H: Local Gemma4 Runtime Plugin

Status:
Completed on 2026-06-30.

Goal:
Use local `gemma4` as the first real LLM-backed evaluation plugin without
breaking the deterministic baseline path.

Scope:

- define a local answer-generation seam that does not replace the current
  baseline answer builder
- implement a `gemma4` plugin for local-only answer generation
- add opt-in `gemma4` smoke/tests using explicit local configuration
- compare plugin-generated answers against baseline artifact shapes

Exit Criteria:

- local `gemma4` can be used for opt-in runtime evaluation
- no `gemma4` dependency is required for the supported baseline path
- plugin outputs still serialize into the existing artifact/review shape

Delivered:

- `AnswerRuntime` now supports an opt-in answer generator seam
- local `gemma4` is registered as a provider plugin with `--answer-plugin gemma4`
- local `gemma4` requests use OpenAI-compatible chat-completions over plain HTTP
- plugin-backed answers preserve the current evaluation artifact shape
- `gemma4` tests are gated behind `--run-provider-plugins --run-gemma4`

## Milestone I: Hosted Provider Plugins and Comparative Evaluation

Goal:
Allow hosted vector or LLM providers to participate in comparative evaluation
through the same plugin surface.

Scope:

- add hosted provider plugins behind the provider interface
- support provider-specific evaluation scenarios without changing baseline smoke
- compare plugin-backed retrieval/runtime outputs against local baseline artifacts
- keep provider assumptions explicit in docs and tests

Exit Criteria:

- hosted provider plugins remain optional
- comparative evaluation can be run without changing core contracts
- plugin failures stay isolated and do not downgrade the baseline path

## Milestone J: Release Automation Beyond Smoke CI

Goal:
Automate release packaging and publication after the plugin seams stabilize.

Scope:

- release note generation from repo artifacts
- tag/release workflow automation
- optional plugin compatibility matrix checks
- smoke promotion rules for release candidates

Exit Criteria:

- release automation reflects the supported boundary clearly
- plugin-specific failures do not block the baseline release unless explicitly required

## Milestone K: Chronicle Write-back Boundary Review

Goal:
Revisit whether any trial-record or downstream review persistence should be
bridged back to Chronicle, and only do so through an explicit boundary review.

Scope:

- define the architectural boundary for optional write-back
- specify non-authoritative vs authoritative record transitions
- determine whether any write-back belongs here or should remain outside this repo

Exit Criteria:

- write-back either remains explicitly out of scope or is accepted through a
  dedicated architecture decision
- no accidental Chronicle mutation path is introduced

## Recommended Execution Order

1. Milestone F: make fixture growth pluggable first
2. Milestone G: isolate provider plugins and credentials second
3. Milestone H: add local `gemma4` as the first real plugin
4. Milestone I: add hosted provider plugins only after the plugin surface is stable
5. Milestone J: automate release flows after the extension boundary is proven
6. Milestone K: revisit write-back last because it changes authority boundaries

## Why This Order

- fixture plugins are low-risk and improve coverage without weakening the boundary
- provider isolation should exist before the first real provider is introduced
- local `gemma4` is a safer first plugin than a hosted service because it avoids
  remote dependency and credential sprawl
- write-back has the highest boundary risk and should remain last
