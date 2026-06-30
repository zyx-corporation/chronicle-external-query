from __future__ import annotations

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-provider-plugins",
        action="store_true",
        default=False,
        help="run opt-in provider plugin tests",
    )
    parser.addoption(
        "--run-hosted-providers",
        action="store_true",
        default=False,
        help="run opt-in hosted provider tests",
    )
    parser.addoption(
        "--run-gemma4",
        action="store_true",
        default=False,
        help="run opt-in local gemma4 plugin tests",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    run_provider_plugins = config.getoption("--run-provider-plugins")
    run_hosted_providers = config.getoption("--run-hosted-providers")
    run_gemma4 = config.getoption("--run-gemma4")
    skip_provider = pytest.mark.skip(reason="provider plugin tests require --run-provider-plugins")
    skip_hosted = pytest.mark.skip(reason="hosted provider tests require --run-hosted-providers")
    skip_gemma4 = pytest.mark.skip(reason="gemma4 tests require --run-gemma4")

    for item in items:
        if "provider_plugin" in item.keywords and not run_provider_plugins:
            item.add_marker(skip_provider)
        if "hosted_provider" in item.keywords and not run_hosted_providers:
            item.add_marker(skip_hosted)
        if "gemma4" in item.keywords and not run_gemma4:
            item.add_marker(skip_gemma4)
