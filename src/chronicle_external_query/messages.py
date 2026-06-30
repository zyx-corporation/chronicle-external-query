from __future__ import annotations

import os
from typing import Any


DEFAULT_LOCALE = "ja"
FALLBACK_LOCALE = "en"
SUPPORTED_LOCALES = {"ja", "en", "zh-CN"}
LOCALE_ENV_VAR = "CHRONICLE_EXTERNAL_QUERY_LOCALE"


CATALOG: dict[str, dict[str, str]] = {
    "en": {
        "cli.validate.success": "Bundle validated successfully.",
        "cli.validate.failure": "Bundle validation failed.",
        "cli.bundle.success": "Bundle loaded successfully.",
        "cli.run.success": "Query executed successfully.",
        "cli.run.failure": "Query execution failed.",
        "cli.run.output_written": "Evaluation artifact written to {path}.",
        "cli.show.success": "Evaluation artifact loaded successfully.",
        "cli.show.failure": "Evaluation artifact loading failed.",
        "cli.compare.success": "Evaluation artifacts compared successfully.",
        "cli.compare.failure": "Evaluation artifact comparison failed.",
        "cli.report.success": "Markdown trial report rendered successfully.",
        "cli.report.output_written": "Markdown trial report written to {path}.",
        "cli.report.failure": "Markdown trial report rendering failed.",
        "cli.compare_report.success": "Markdown comparison report rendered successfully.",
        "cli.compare_report.output_written": "Markdown comparison report written to {path}.",
        "cli.compare_report.failure": "Markdown comparison report rendering failed.",
        "cli.label.bundle_dir": "Bundle directory",
        "cli.label.query": "Query",
        "cli.label.mode": "Mode",
        "cli.label.status": "Status",
        "cli.label.match_count": "Match count",
        "cli.label.sufficient": "Sufficient",
        "cli.label.missing_behavior": "Missing behavior",
    },
    "ja": {
        "cli.validate.success": "Bundle validation completed successfully.",
        "cli.validate.failure": "Bundle validation failed.",
        "cli.bundle.success": "Bundle loaded successfully.",
        "cli.run.success": "Query execution completed successfully.",
        "cli.run.failure": "Query execution failed.",
        "cli.run.output_written": "Evaluation artifact written to {path}.",
        "cli.show.success": "Evaluation artifact loaded successfully.",
        "cli.show.failure": "Evaluation artifact loading failed.",
        "cli.compare.success": "Evaluation artifacts compared successfully.",
        "cli.compare.failure": "Evaluation artifact comparison failed.",
        "cli.report.success": "Markdown trial report rendered successfully.",
        "cli.report.output_written": "Markdown trial report written to {path}.",
        "cli.report.failure": "Markdown trial report rendering failed.",
        "cli.compare_report.success": "Markdown comparison report rendered successfully.",
        "cli.compare_report.output_written": "Markdown comparison report written to {path}.",
        "cli.compare_report.failure": "Markdown comparison report rendering failed.",
        "cli.label.bundle_dir": "Bundle directory",
        "cli.label.query": "Query",
        "cli.label.mode": "Mode",
        "cli.label.status": "Status",
        "cli.label.match_count": "Match count",
        "cli.label.sufficient": "Sufficient",
        "cli.label.missing_behavior": "Missing behavior",
    },
    "zh-CN": {
        "cli.validate.success": "Bundle validation completed successfully.",
        "cli.validate.failure": "Bundle validation failed.",
        "cli.bundle.success": "Bundle loaded successfully.",
        "cli.run.success": "Query execution completed successfully.",
        "cli.run.failure": "Query execution failed.",
        "cli.run.output_written": "Evaluation artifact written to {path}.",
        "cli.show.success": "Evaluation artifact loaded successfully.",
        "cli.show.failure": "Evaluation artifact loading failed.",
        "cli.compare.success": "Evaluation artifacts compared successfully.",
        "cli.compare.failure": "Evaluation artifact comparison failed.",
        "cli.report.success": "Markdown trial report rendered successfully.",
        "cli.report.output_written": "Markdown trial report written to {path}.",
        "cli.report.failure": "Markdown trial report rendering failed.",
        "cli.compare_report.success": "Markdown comparison report rendered successfully.",
        "cli.compare_report.output_written": "Markdown comparison report written to {path}.",
        "cli.compare_report.failure": "Markdown comparison report rendering failed.",
        "cli.label.bundle_dir": "Bundle directory",
        "cli.label.query": "Query",
        "cli.label.mode": "Mode",
        "cli.label.status": "Status",
        "cli.label.match_count": "Match count",
        "cli.label.sufficient": "Sufficient",
        "cli.label.missing_behavior": "Missing behavior",
    },
}


def resolve_locale(locale: str | None) -> str:
    candidate = locale or os.getenv(LOCALE_ENV_VAR)
    if candidate in SUPPORTED_LOCALES:
        return str(candidate)
    return DEFAULT_LOCALE


def message(key: str, *, locale: str | None = None, **params: Any) -> str:
    resolved_locale = resolve_locale(locale)
    template = CATALOG.get(resolved_locale, {}).get(key)
    if template is None:
        template = CATALOG[FALLBACK_LOCALE].get(key, key)
    return template.format(**params)
