from __future__ import annotations

import pytest

from chronicle_external_query.plugins import load_provider_plugin


pytestmark = [pytest.mark.provider_plugin]


def test_static_test_provider_becomes_available_when_credential_env_is_present(monkeypatch):
    monkeypatch.setenv(
        "CHRONICLE_EXTERNAL_QUERY_STATIC_TEST_PROVIDER_API_KEY",
        "fixture-provider-key",
    )

    plugin = load_provider_plugin("static-test-provider")
    status = plugin.describe_status()

    assert plugin.is_available() is True
    assert status.available is True
    assert status.availability_reason == "configured"
    assert status.config_fields[0].secret is True
    assert status.metadata["runtime_integration"] == "not_enabled_until_milestone_h"
