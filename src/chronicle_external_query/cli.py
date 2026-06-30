from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from chronicle_external_query.evaluation.artifacts import (
    build_chronicle_trial_alignment,
    compare_evaluation_artifacts,
    build_evaluation_artifact,
    load_evaluation_artifact,
    render_markdown_comparison_report,
    render_markdown_trial_report,
    save_evaluation_artifact,
)
from chronicle_external_query.fixtures import FixtureRegistry, FixtureRegistryError
from chronicle_external_query.ingest.handoff_loader import HandoffLoader
from chronicle_external_query.messages import DEFAULT_LOCALE, SUPPORTED_LOCALES, message, resolve_locale
from chronicle_external_query.models import ImportValidationError
from chronicle_external_query.plugins import (
    ProviderPluginError,
    list_provider_plugin_statuses,
)
from chronicle_external_query.retrieval.vector_adapter import load_static_vector_retriever
from chronicle_external_query.runtime.answer_runtime import AnswerRuntime


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    locale = resolve_locale(getattr(args, "locale", None))

    try:
        if args.command == "validate-bundle":
            return _validate_bundle(args=args, locale=locale)
        if args.command == "show-bundle":
            return _show_bundle(args=args, locale=locale)
        if args.command == "run-query":
            return _run_query(args=args, locale=locale)
        if args.command == "show-artifact":
            return _show_artifact(args=args, locale=locale)
        if args.command == "compare-artifacts":
            return _compare_artifacts(args=args, locale=locale)
        if args.command == "list-fixtures":
            return _list_fixtures(args=args, locale=locale)
        if args.command == "list-plugins":
            return _list_plugins(args=args, locale=locale)
        if args.command == "render-artifact-report":
            return _render_artifact_report(args=args, locale=locale)
        if args.command == "render-comparison-report":
            return _render_comparison_report(args=args, locale=locale)
    except ImportValidationError as exc:
        return _emit_error(
            summary_key=_failure_summary_key(args.command),
            locale=locale,
            error=exc,
            as_json=args.json,
        )
    except FixtureRegistryError as exc:
        return _emit_registry_error(error=exc, locale=locale, as_json=args.json)
    except ProviderPluginError as exc:
        return _emit_plugin_error(error=exc, locale=locale, as_json=args.json)

    parser.print_help()
    return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="chronicle-external-query")
    subparsers = parser.add_subparsers(dest="command")

    validate = subparsers.add_parser("validate-bundle")
    validate.add_argument("bundle_dir")
    validate.add_argument("--locale", choices=sorted(SUPPORTED_LOCALES))
    validate.add_argument("--json", action="store_true")

    show_bundle = subparsers.add_parser("show-bundle")
    show_bundle.add_argument("bundle_dir")
    show_bundle.add_argument("--locale", choices=sorted(SUPPORTED_LOCALES))
    show_bundle.add_argument("--json", action="store_true")

    run = subparsers.add_parser("run-query")
    run.add_argument("bundle_dir")
    run.add_argument("--query", required=True)
    run.add_argument("--mode", choices=["graph", "hybrid"], default="graph")
    run.add_argument("--vector-fixture")
    run.add_argument("--reviewer", default="local-reviewer")
    run.add_argument("--consumer", default="local-consumer")
    run.add_argument("--output")
    run.add_argument("--locale", choices=sorted(SUPPORTED_LOCALES))
    run.add_argument("--json", action="store_true")

    show = subparsers.add_parser("show-artifact")
    show.add_argument("artifact_path")
    show.add_argument("--locale", choices=sorted(SUPPORTED_LOCALES))
    show.add_argument("--json", action="store_true")

    compare = subparsers.add_parser("compare-artifacts")
    compare.add_argument("left_artifact_path")
    compare.add_argument("right_artifact_path")
    compare.add_argument("--locale", choices=sorted(SUPPORTED_LOCALES))
    compare.add_argument("--json", action="store_true")

    fixtures = subparsers.add_parser("list-fixtures")
    fixtures.add_argument(
        "--fixture-dir",
        action="append",
        default=[],
        help="optional fixture pack directory containing fixture-pack.json",
    )
    fixtures.add_argument(
        "--no-env-fixture-dirs",
        action="store_true",
        help="ignore optional fixture directories from CHRONICLE_EXTERNAL_QUERY_FIXTURE_DIRS",
    )
    fixtures.add_argument("--locale", choices=sorted(SUPPORTED_LOCALES))
    fixtures.add_argument("--json", action="store_true")

    plugins = subparsers.add_parser("list-plugins")
    plugins.add_argument("--locale", choices=sorted(SUPPORTED_LOCALES))
    plugins.add_argument("--json", action="store_true")

    report = subparsers.add_parser("render-artifact-report")
    report.add_argument("artifact_path")
    report.add_argument("--output")
    report.add_argument("--locale", choices=sorted(SUPPORTED_LOCALES))
    report.add_argument("--json", action="store_true")

    compare_report = subparsers.add_parser("render-comparison-report")
    compare_report.add_argument("left_artifact_path")
    compare_report.add_argument("right_artifact_path")
    compare_report.add_argument("--output")
    compare_report.add_argument("--locale", choices=sorted(SUPPORTED_LOCALES))
    compare_report.add_argument("--json", action="store_true")
    return parser


def _validate_bundle(*, args: argparse.Namespace, locale: str) -> int:
    bundle = HandoffLoader().load_bundle(Path(args.bundle_dir))
    payload = {
        "status": "validated",
        "summary": message("cli.validate.success", locale=locale),
        "bundle_dir": str(bundle.paths.bundle_dir),
        "bundle_kind": bundle.manifest_payload["bundle_kind"],
        "contract_versions": {
            "bundle_manifest": bundle.manifest_payload["contract_version"],
            "handoff": bundle.handoff_payload["contract_version"],
            "graph_export": bundle.graph_payload["export_contract"]["contract_version"],
            "adapter_skeleton": bundle.adapter_skeleton_payload["contract_version"],
        },
        "files": bundle.manifest_payload["files"],
        "primary_record_path": bundle.manifest_payload["primary_record_path"],
    }
    return _emit_result(payload=payload, as_json=args.json)


def _show_bundle(*, args: argparse.Namespace, locale: str) -> int:
    bundle = HandoffLoader().load_bundle(Path(args.bundle_dir))
    payload = {
        "status": "bundle_loaded",
        "summary": message("cli.bundle.success", locale=locale),
        **_build_bundle_summary(bundle),
        "files": bundle.manifest_payload["files"],
    }
    return _emit_result(payload=payload, as_json=args.json)


def _run_query(*, args: argparse.Namespace, locale: str) -> int:
    bundle = HandoffLoader().load_bundle(Path(args.bundle_dir))
    vector_retriever = (
        load_static_vector_retriever(Path(args.vector_fixture))
        if args.vector_fixture
        else None
    )
    runtime = AnswerRuntime(mode=args.mode, vector_retriever=vector_retriever)
    answer = runtime.answer(bundle.graph_payload, query=args.query)
    artifact = build_evaluation_artifact(
        answer,
        reviewer=args.reviewer,
        downstream_consumer=args.consumer,
        files_reviewed=["query_engine_handoff.json", "graph.json", "bundle_manifest.json"],
        bundle_summary=_build_bundle_summary(bundle),
    )
    if args.output:
        save_evaluation_artifact(artifact, Path(args.output))
    payload: dict[str, Any] = {
        "status": "executed",
        "summary": message("cli.run.success", locale=locale),
        "bundle_dir": str(bundle.paths.bundle_dir),
        "query": args.query,
        "mode": args.mode,
        "vector_fixture": str(Path(args.vector_fixture)) if args.vector_fixture else "",
        "runtime_status": answer.status,
        "answer_text": answer.answer_text,
        "match_count": len(answer.graph_matches),
        "sufficient": artifact.sufficient,
        "missing_behavior": artifact.missing_behavior,
        "artifact": {
            "artifact_version": artifact.artifact_version,
            "reviewer": artifact.reviewer,
            "downstream_consumer": artifact.downstream_consumer,
            "files_reviewed": artifact.files_reviewed,
            "bundle_summary": artifact.bundle_summary,
        },
        "chronicle_trial_alignment": build_chronicle_trial_alignment(artifact),
    }
    if args.output:
        payload["output_path"] = str(Path(args.output))
        payload["output_summary"] = message("cli.run.output_written", locale=locale, path=str(Path(args.output)))
    return _emit_result(payload=payload, as_json=args.json)


def _show_artifact(*, args: argparse.Namespace, locale: str) -> int:
    artifact = load_evaluation_artifact(Path(args.artifact_path))
    payload: dict[str, Any] = {
        "status": "artifact_loaded",
        "summary": message("cli.show.success", locale=locale),
        "artifact_path": str(Path(args.artifact_path)),
        "query": artifact.query,
        "runtime_status": artifact.runtime_status,
        "retrieval_mode": artifact.retrieval_mode,
        "sufficient": artifact.sufficient,
        "missing_behavior": artifact.missing_behavior,
        "match_count": len(artifact.matches),
        "source_match_counts": artifact.provenance.get("source_match_counts", {}),
        "overlap_source_record_ids": artifact.provenance.get("overlap_source_record_ids", []),
        "insufficiency_reasons": artifact.provenance.get("insufficiency_reasons", []),
        "reviewer": artifact.reviewer,
        "downstream_consumer": artifact.downstream_consumer,
        "files_reviewed": artifact.files_reviewed,
        "bundle_summary": artifact.bundle_summary,
        "chronicle_trial_alignment": build_chronicle_trial_alignment(artifact),
    }
    return _emit_result(payload=payload, as_json=args.json)


def _compare_artifacts(*, args: argparse.Namespace, locale: str) -> int:
    left = load_evaluation_artifact(Path(args.left_artifact_path))
    right = load_evaluation_artifact(Path(args.right_artifact_path))
    comparison = compare_evaluation_artifacts(left, right)
    payload: dict[str, Any] = {
        "status": "artifacts_compared",
        "summary": message("cli.compare.success", locale=locale),
        "left_artifact_path": str(Path(args.left_artifact_path)),
        "right_artifact_path": str(Path(args.right_artifact_path)),
        "comparison_summary": _build_comparison_summary(comparison),
        "comparison": comparison,
    }
    return _emit_result(payload=payload, as_json=args.json)


def _list_fixtures(*, args: argparse.Namespace, locale: str) -> int:
    registry = FixtureRegistry.default(
        fixture_dirs=[Path(path) for path in args.fixture_dir],
        include_env_fixture_dirs=not args.no_env_fixture_dirs,
    )
    fixture_sets = registry.list_fixture_sets()
    payload: dict[str, Any] = {
        "status": "fixtures_loaded",
        "summary": message("cli.fixtures.success", locale=locale),
        "fixture_count": len(fixture_sets),
        "fixtures": [
            {
                "fixture_id": fixture_set.fixture_id,
                "source_name": fixture_set.source_name,
                "fixture_kind": fixture_set.fixture_kind,
                "bundle_dir": str(fixture_set.bundle_dir),
                "vector_fixture": (
                    str(fixture_set.vector_fixture_path) if fixture_set.vector_fixture_path else ""
                ),
                "is_baseline": fixture_set.is_baseline,
                "metadata": fixture_set.metadata,
            }
            for fixture_set in fixture_sets
        ],
    }
    return _emit_result(payload=payload, as_json=args.json)


def _list_plugins(*, args: argparse.Namespace, locale: str) -> int:
    statuses = list_provider_plugin_statuses()
    payload: dict[str, Any] = {
        "status": "plugins_loaded",
        "summary": message("cli.plugins.success", locale=locale),
        "plugin_count": len(statuses),
        "plugins": [
            {
                "plugin_name": status.plugin_name,
                "available": status.available,
                "availability_reason": status.availability_reason,
                "config_fields": [
                    {
                        "key": field.key,
                        "env_var": field.env_var,
                        "required": field.required,
                        "secret": field.secret,
                        "description": field.description,
                    }
                    for field in status.config_fields
                ],
                "metadata": status.metadata,
            }
            for status in statuses
        ],
    }
    return _emit_result(payload=payload, as_json=args.json)


def _render_artifact_report(*, args: argparse.Namespace, locale: str) -> int:
    artifact = load_evaluation_artifact(Path(args.artifact_path))
    markdown = render_markdown_trial_report(artifact)
    payload: dict[str, Any] = {
        "status": "report_rendered",
        "summary": message("cli.report.success", locale=locale),
        "artifact_path": str(Path(args.artifact_path)),
        "runtime_status": artifact.runtime_status,
        "retrieval_mode": artifact.retrieval_mode,
        "sufficient": artifact.sufficient,
        "match_count": len(artifact.matches),
        "markdown_line_count": len(markdown.splitlines()),
        "markdown": markdown,
    }
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(markdown, encoding="utf-8")
        payload["output_path"] = str(output_path)
        payload["output_summary"] = message("cli.report.output_written", locale=locale, path=str(output_path))
    return _emit_result(payload=payload, as_json=args.json)


def _render_comparison_report(*, args: argparse.Namespace, locale: str) -> int:
    left = load_evaluation_artifact(Path(args.left_artifact_path))
    right = load_evaluation_artifact(Path(args.right_artifact_path))
    comparison = compare_evaluation_artifacts(left, right)
    markdown = render_markdown_comparison_report(left, right)
    payload: dict[str, Any] = {
        "status": "comparison_report_rendered",
        "summary": message("cli.compare_report.success", locale=locale),
        "left_artifact_path": str(Path(args.left_artifact_path)),
        "right_artifact_path": str(Path(args.right_artifact_path)),
        "comparison_summary": {
            "runtime_status_changed": comparison["runtime_status_changed"],
            "retrieval_mode_changed": comparison["retrieval_mode_changed"],
            "sufficiency_changed": comparison["sufficiency_changed"],
            "match_count_delta": comparison["match_count_delta"],
            "bundle_summary_changed": comparison["bundle_summary_changed"],
            "contract_versions_changed": comparison["contract_versions_changed"],
            "graph_stats_changed": comparison["graph_stats_changed"],
        },
        "markdown_line_count": len(markdown.splitlines()),
        "markdown": markdown,
    }
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(markdown, encoding="utf-8")
        payload["output_path"] = str(output_path)
        payload["output_summary"] = message(
            "cli.compare_report.output_written",
            locale=locale,
            path=str(output_path),
        )
    return _emit_result(payload=payload, as_json=args.json)


def _emit_error(*, summary_key: str, locale: str, error: ImportValidationError, as_json: bool) -> int:
    payload = {
        "status": "error",
        "summary": message(summary_key, locale=locale),
        "error": str(error),
        "error_code": error.error_code,
        "error_category": error.error_category,
    }
    return _emit_result(payload=payload, as_json=as_json, exit_code=1)


def _emit_registry_error(*, error: FixtureRegistryError, locale: str, as_json: bool) -> int:
    payload = {
        "status": "error",
        "summary": message("cli.fixtures.failure", locale=locale),
        "error": str(error),
        "error_code": "fixture_registry.invalid_configuration",
        "error_category": "fixture_registry",
    }
    return _emit_result(payload=payload, as_json=as_json, exit_code=1)


def _emit_plugin_error(*, error: ProviderPluginError, locale: str, as_json: bool) -> int:
    payload = {
        "status": "error",
        "summary": message("cli.plugins.failure", locale=locale),
        "error": str(error),
        "error_code": "provider_plugin.invalid_configuration",
        "error_category": "provider_plugin",
    }
    return _emit_result(payload=payload, as_json=as_json, exit_code=1)


def _emit_result(*, payload: dict[str, Any], as_json: bool, exit_code: int = 0) -> int:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for key, value in payload.items():
            if isinstance(value, (dict, list)):
                print(f"{key}: {json.dumps(value, ensure_ascii=False)}")
            else:
                print(f"{key}: {value}")
    return exit_code


def _failure_summary_key(command: str | None) -> str:
    mapping = {
        "validate-bundle": "cli.validate.failure",
        "show-bundle": "cli.validate.failure",
        "run-query": "cli.run.failure",
        "show-artifact": "cli.show.failure",
        "compare-artifacts": "cli.compare.failure",
        "list-fixtures": "cli.fixtures.failure",
        "list-plugins": "cli.plugins.failure",
        "render-artifact-report": "cli.report.failure",
        "render-comparison-report": "cli.compare_report.failure",
    }
    return mapping.get(command, "cli.run.failure")


def _build_bundle_summary(bundle: Any) -> dict[str, Any]:
    return {
        "bundle_dir": str(bundle.paths.bundle_dir),
        "bundle_kind": bundle.manifest_payload["bundle_kind"],
        "contract_versions": {
            "bundle_manifest": bundle.manifest_payload["contract_version"],
            "handoff": bundle.handoff_payload["contract_version"],
            "graph_export": bundle.graph_payload["export_contract"]["contract_version"],
            "adapter_skeleton": bundle.adapter_skeleton_payload["contract_version"],
        },
        "primary_record_path": bundle.manifest_payload["primary_record_path"],
        "primary_record_present": bundle.paths.primary_record_jsonl is not None,
        "import_ready": bool(bundle.manifest_payload["import_ready"]),
        "import_validation_status": bundle.manifest_payload["import_validation_status"],
        "graph_stats": {
            "node_count": len(bundle.graph_payload.get("nodes", [])),
            "edge_count": len(bundle.graph_payload.get("edges", [])),
        },
    }


def _build_comparison_summary(comparison: dict[str, Any]) -> dict[str, Any]:
    changed_fields = [
        field
        for field in (
            "runtime_status_changed",
            "retrieval_mode_changed",
            "sufficiency_changed",
            "missing_behavior_changed",
            "insufficiency_changed",
            "bundle_summary_changed",
            "bundle_kind_changed",
            "primary_record_path_changed",
            "contract_versions_changed",
            "graph_stats_changed",
        )
        if comparison.get(field) is True
    ]
    return {
        "changed_fields": changed_fields,
        "difference_count": len(changed_fields),
        "match_count_delta": comparison.get("match_count_delta", 0),
        "query_matches": comparison.get("query_matches", False),
    }


if __name__ == "__main__":
    sys.exit(main())
