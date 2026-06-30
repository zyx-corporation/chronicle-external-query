# Pluggable Extension Specification

This document describes the proposed extension architecture for post-`v0.2.0`
work, with special attention to:

- pluggable fixture expansion
- pluggable provider-backed tests
- a local `gemma4` initial runtime plugin

## Design Goals

- preserve the current `v0.2.0` local-only baseline as the default path
- keep provider SDKs, credentials, and hosted assumptions out of core imports
- allow new fixture suites and provider plugins without rewriting the baseline
- keep evaluation artifacts and review reports stable across baseline and plugin paths

## Non-Goals

- replacing the current deterministic baseline answer path
- making hosted providers mandatory
- introducing Chronicle write-back through plugin loading
- making baseline CI depend on local `gemma4` availability

## Proposed Core Extension Points

### 1. Fixture Source Protocol

Current implementation status:
Milestone F is now implemented for the fixture side of this specification. The
repository ships `chronicle_external_query.fixtures.FixtureRegistry`, two
committed baseline fixture registrations, and manifest-driven optional fixture
pack loading through `fixture-pack.json`.

Purpose:
Load optional fixture suites without hardcoding every future bundle under
`tests/fixtures/`.

Suggested shape:

```python
class FixtureSourceProtocol(Protocol):
    source_name: str

    def list_fixture_sets(self) -> list["FixtureSet"]:
        ...

    def load_fixture_set(self, fixture_id: str) -> "FixtureSet":
        ...
```

Suggested supporting dataclasses:

```python
@dataclass(frozen=True)
class FixtureSet:
    fixture_id: str
    source_name: str
    fixture_kind: str
    bundle_dir: Path
    metadata: dict[str, Any]
```

Core rule:
The default test suite continues to use committed baseline fixtures directly.
The registry is for optional fixture packs, not for replacing the baseline.

Implemented manifest shape:

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

### 2. Answer Generator Protocol

Current implementation status:
Milestone H is now implemented for the first local answer generator. The
repository ships `GeneratedAnswer`, `AnswerGeneratorProtocol`, an opt-in answer
generator seam in `AnswerRuntime`, and a local `gemma4` plugin that uses an
OpenAI-compatible chat-completions endpoint.

Purpose:
Allow local `gemma4` or other future LLM-backed answer generation without
replacing the current deterministic answer builder.

Suggested shape:

```python
class AnswerGeneratorProtocol(Protocol):
    generator_name: str

    def generate(
        self,
        *,
        query: str,
        matches: list[RetrievalMatch],
        provenance: RetrievalProvenance,
        prompt: str,
    ) -> "GeneratedAnswer":
        ...
```

Suggested supporting dataclass:

```python
@dataclass(frozen=True)
class GeneratedAnswer:
    status: str
    answer_text: str
    metadata: dict[str, Any]
```

Core rule:
`AnswerRuntime` should continue to work with its built-in deterministic answer
path when no plugin is provided.

### 3. Provider Plugin Protocol

Current implementation status:
Milestone G is now implemented for provider plugin registration and credential
isolation. The repository ships `chronicle_external_query.plugins`, an explicit
provider plugin loader, `list-plugins`, and plugin-specific environment-variable
configuration reporting. Runtime answer generation remains on the deterministic
built-in path unless an explicit plugin is requested.

Purpose:
Load optional provider-backed runtime or evaluation adapters with explicit
configuration.

Suggested shape:

```python
class ProviderPluginProtocol(Protocol):
    plugin_name: str

    def is_available(self) -> bool:
        ...

    def describe_configuration(self) -> dict[str, Any]:
        ...
```

Provider-specific runtime plugins may also implement:

- `AnswerGeneratorProtocol`
- vector retrieval protocols
- optional smoke hooks

Current built-in registry entry:

- `gemma4`
- required env vars:
  `GEMMA4_ENABLED`, `GEMMA4_BASE_URL`, `GEMMA4_MODEL`
- optional env vars:
  `GEMMA4_TIMEOUT`, `GEMMA4_API_KEY`
- runtime integration:
  active for opt-in answer generation
- `openai-compatible-hosted`
- required env vars:
  `OPENAI_COMPATIBLE_HOSTED_ENABLED`,
  `OPENAI_COMPATIBLE_HOSTED_BASE_URL`,
  `OPENAI_COMPATIBLE_HOSTED_MODEL`,
  `OPENAI_COMPATIBLE_HOSTED_API_KEY`
- optional env var:
  `OPENAI_COMPATIBLE_HOSTED_TIMEOUT`
- runtime integration:
  active for opt-in hosted answer generation and comparative evaluation
- `static-test-provider`
- required credential env var:
  `CHRONICLE_EXTERNAL_QUERY_STATIC_TEST_PROVIDER_API_KEY`
- optional endpoint env var:
  `CHRONICLE_EXTERNAL_QUERY_STATIC_TEST_PROVIDER_ENDPOINT`
- runtime integration:
  reserved only

## Proposed Package Layout

Suggested post-`v0.2.0` additions:

```text
src/chronicle_external_query/
  fixtures/
    registry.py
    contracts.py
  plugins/
    contracts.py
    loader.py
    gemma4/
      config.py
      answer_generator.py
tests/
  providers/
    test_gemma4_plugin.py
```

## Local Gemma4 Plugin

### Scope

The first plugin should target local `gemma4` usage only.

### Why local Gemma4 first

- keeps the first real LLM plugin local-first
- avoids hosted-provider credentials during early plugin work
- preserves the current repository boundary more cleanly than a hosted service

### Proposed config

Environment variables:

- `GEMMA4_BASE_URL`
- `GEMMA4_MODEL`
- `GEMMA4_TIMEOUT`
- `GEMMA4_ENABLED`

Optional CLI/config flags later:

- `--answer-plugin gemma4`
- `--provider-config path/to/config.json`

### Runtime behavior

- if `gemma4` is not configured, the plugin is unavailable and should be skipped
- if the plugin is configured but fails, the failure should remain explicit and
  should not silently mutate the baseline path
- plugin-generated answers should still serialize into the current
  `EvaluationArtifact` shape

### Metadata expectations

When plugin-backed generation is used, metadata should make that explicit, for
example:

- `answer_generator: gemma4`
- `answer_generator_mode: local_plugin`
- `answer_generator_fallback_used: false`

## Testing Model

### Baseline tests

Remain unchanged:

- `pytest`
- `bash scripts/smoke_clean_checkout.sh`
- `chronicle-external-query list-fixtures --json --no-env-fixture-dirs`
- `chronicle-external-query list-plugins --json`

These must not require plugins, credentials, or local model availability.

### Opt-in provider tests

Suggested separation:

- `pytest -m provider_plugin`
- `pytest tests/providers/`
- `pytest --run-gemma4`
- `pytest --run-provider-plugins tests/providers/`
- `pytest --run-hosted-providers -m hosted_provider`
- `pytest --run-provider-plugins --run-gemma4 tests/providers/test_gemma4_plugin.py`
- `pytest --run-provider-plugins --run-hosted-providers tests/providers/test_openai_compatible_hosted_plugin.py`

Suggested markers:

- `provider_plugin`
- `gemma4`
- `hosted_provider`

Rule:
If required config is absent, provider tests should skip, not fail the baseline.

## Fixture Registry Model

Suggested fixture categories:

- `baseline_minimal`
- `baseline_representative`
- `optional_chronicle_real_bundle_pack`
- `optional_provider_comparison_pack`

Fixture metadata should record:

- origin
- sanitization status
- intended test scope
- whether the fixture belongs to the default baseline

## Failure Handling Rules

- plugin load failure should be explicit and isolated
- credential absence should produce a skip or unavailable state, not a baseline error
- fixture plugin drift should not break the committed baseline fixture path
- plugin outputs must never be presented as Chronicle-authoritative

## Documentation Requirements

Any future implementation of this spec should update:

- `README.md`
- `README.ja.md`
- `docs/testing-strategy.md`
- `docs/operator-runbook.md`
- `docs/releases/`
- `docs/runtime-answer-contract.md`
- `docs/retrieval-contract.md` when retrieval plugins change result semantics

## Milestone Mapping

- Milestone F: fixture registry and optional fixture packs
- Milestone G: provider plugin surface and credential isolation
- Milestone H: local `gemma4` runtime plugin
- Milestone I: hosted provider plugins
- Milestone J: release automation for the extension track
- Milestone K: Chronicle write-back boundary review
