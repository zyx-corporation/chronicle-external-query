from __future__ import annotations

from chronicle_external_query.messages import (
    DEFAULT_LOCALE,
    FALLBACK_LOCALE,
    LOCALE_ENV_VAR,
    message,
    resolve_locale,
)


def test_resolve_locale_returns_default_for_unknown_locale():
    assert resolve_locale("fr") == DEFAULT_LOCALE


def test_message_falls_back_to_english_when_key_missing_from_locale_catalog():
    assert message("cli.validate.success", locale="ja") == "Bundle validation completed successfully."
    assert message("nonexistent.key", locale="ja") == "nonexistent.key"
    assert message("cli.validate.success", locale="unknown") == message(
        "cli.validate.success",
        locale=DEFAULT_LOCALE,
    )


def test_message_catalog_uses_expected_fallback_locale():
    assert FALLBACK_LOCALE == "en"
    assert message("cli.run.success", locale="en") == "Query executed successfully."
    assert message("cli.bundle.success", locale="en") == "Bundle loaded successfully."
    assert message("cli.compare_report.success", locale="en") == "Markdown comparison report rendered successfully."
    assert message("cli.show.failure", locale="en") == "Evaluation artifact loading failed."


def test_resolve_locale_uses_environment_variable(monkeypatch):
    monkeypatch.setenv(LOCALE_ENV_VAR, "zh-CN")
    assert resolve_locale(None) == "zh-CN"
