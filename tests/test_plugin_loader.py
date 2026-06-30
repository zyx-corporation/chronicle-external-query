from __future__ import annotations

from chronicle_external_query.plugins import (
    ProviderPluginNotFoundError,
    list_provider_plugin_definitions,
    list_provider_plugin_statuses,
    load_provider_plugin,
)


def test_list_provider_plugin_definitions_exposes_registered_plugins():
    definitions = list_provider_plugin_definitions()

    assert [definition.plugin_name for definition in definitions] == [
        "gemma4",
        "openai-compatible-hosted",
        "static-test-provider",
    ]
    assert definitions[0].module_path.endswith("gemma4_local")


def test_list_provider_plugin_statuses_reports_unavailable_plugin_without_credentials(monkeypatch):
    monkeypatch.delenv("CHRONICLE_EXTERNAL_QUERY_STATIC_TEST_PROVIDER_API_KEY", raising=False)
    monkeypatch.delenv("GEMMA4_ENABLED", raising=False)
    monkeypatch.delenv("GEMMA4_BASE_URL", raising=False)
    monkeypatch.delenv("GEMMA4_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_COMPATIBLE_HOSTED_ENABLED", raising=False)
    monkeypatch.delenv("OPENAI_COMPATIBLE_HOSTED_BASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_COMPATIBLE_HOSTED_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_COMPATIBLE_HOSTED_API_KEY", raising=False)

    statuses = list_provider_plugin_statuses()

    assert len(statuses) == 3
    assert statuses[0].plugin_name == "gemma4"
    assert statuses[0].available is False
    assert statuses[0].availability_reason == "GEMMA4_ENABLED is not enabled"
    assert statuses[0].metadata["runtime_integration"] == "answer_generation_enabled"
    assert statuses[1].plugin_name == "openai-compatible-hosted"
    assert statuses[1].available is False
    assert statuses[1].availability_reason == "OPENAI_COMPATIBLE_HOSTED_ENABLED is not enabled"
    assert statuses[1].metadata["hosting_mode"] == "hosted"
    assert statuses[2].plugin_name == "static-test-provider"
    assert statuses[2].available is False
    assert "missing required credential env var" in statuses[2].availability_reason
    assert statuses[2].metadata["credential_mode"] == "env_only"


def test_load_provider_plugin_rejects_unknown_name():
    try:
        load_provider_plugin("missing-provider")
    except ProviderPluginNotFoundError as exc:
        assert "provider plugin is not registered" in str(exc)
    else:
        raise AssertionError("expected ProviderPluginNotFoundError")
