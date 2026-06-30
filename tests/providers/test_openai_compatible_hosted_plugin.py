from __future__ import annotations

import pytest

from chronicle_external_query.plugins import load_provider_plugin


pytestmark = [pytest.mark.provider_plugin, pytest.mark.hosted_provider]


def test_hosted_plugin_becomes_available_with_hosted_config(monkeypatch):
    monkeypatch.setenv("OPENAI_COMPATIBLE_HOSTED_ENABLED", "true")
    monkeypatch.setenv("OPENAI_COMPATIBLE_HOSTED_BASE_URL", "https://api.example.test")
    monkeypatch.setenv("OPENAI_COMPATIBLE_HOSTED_MODEL", "hosted-model")
    monkeypatch.setenv("OPENAI_COMPATIBLE_HOSTED_API_KEY", "hosted-key")

    plugin = load_provider_plugin("openai-compatible-hosted")
    status = plugin.describe_status()

    assert plugin.is_available() is True
    assert status.available is True
    assert status.availability_reason == "configured"
    assert status.metadata["hosting_mode"] == "hosted"
