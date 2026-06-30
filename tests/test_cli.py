from __future__ import annotations

import json
import os
import subprocess
import sys
import sysconfig
import threading
from pathlib import Path
from shutil import which
import site
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


FIXTURE_BUNDLE_DIR = (
    Path(__file__).resolve().parent / "fixtures" / "query_engine_bundle" / "minimal_cli_bundle"
)
VECTOR_FIXTURE_PATH = (
    Path(__file__).resolve().parent / "fixtures" / "vector_matches" / "sample-vector-matches.json"
)
REPRESENTATIVE_FIXTURE_BUNDLE_DIR = (
    Path(__file__).resolve().parent / "fixtures" / "query_engine_bundle" / "representative_cli_bundle"
)
REPRESENTATIVE_VECTOR_FIXTURE_PATH = (
    Path(__file__).resolve().parent / "fixtures" / "vector_matches" / "representative-vector-matches.json"
)


def _run_cli(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    return subprocess.run(
        [sys.executable, "-m", "chronicle_external_query.cli", *args],
        check=False,
        capture_output=True,
        text=True,
        env=merged_env,
    )


def _run_installed_cli(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    executable = _resolve_installed_cli()
    return subprocess.run(
        [str(executable), *args],
        check=False,
        capture_output=True,
        text=True,
        env=merged_env,
    )


def _resolve_installed_cli() -> Path:
    direct = which("chronicle-external-query")
    if direct:
        return Path(direct)

    candidates = [
        Path(sysconfig.get_path("scripts")) / "chronicle-external-query",
        Path(site.getuserbase()) / "bin" / "chronicle-external-query",
        Path(sys.executable).resolve().parent / "chronicle-external-query",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("chronicle-external-query script was not found in PATH or known script directories")


def test_validate_bundle_cli_json_output():
    result = _run_cli("validate-bundle", str(FIXTURE_BUNDLE_DIR), "--json", "--locale", "en")

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "validated"
    assert payload["bundle_kind"] == "query_engine_handoff_bundle"
    assert payload["contract_versions"]["handoff"] == "1.0"


def test_show_bundle_cli_json_output():
    result = _run_cli("show-bundle", str(FIXTURE_BUNDLE_DIR), "--json", "--locale", "en")

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "bundle_loaded"
    assert payload["bundle_kind"] == "query_engine_handoff_bundle"
    assert payload["graph_stats"]["node_count"] >= 1
    assert payload["graph_stats"]["edge_count"] >= 0
    assert payload["primary_record_present"] is False
    assert payload["primary_record_path"].endswith(".chronicle/chronicle.jsonl")


def test_list_fixtures_cli_returns_baseline_registry():
    result = _run_cli("list-fixtures", "--json", "--locale", "en", "--no-env-fixture-dirs")

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "fixtures_loaded"
    assert payload["fixture_count"] == 2
    assert [fixture["fixture_id"] for fixture in payload["fixtures"]] == [
        "baseline_minimal",
        "baseline_representative",
    ]


def test_list_fixtures_cli_accepts_optional_fixture_pack(tmp_path: Path):
    pack_dir = tmp_path / "fixture-pack"
    pack_dir.mkdir()
    (pack_dir / "fixture-pack.json").write_text(
        json.dumps(
            {
                "manifest_version": "1.0",
                "source_name": "cli_optional_pack",
                "fixtures": [
                    {
                        "fixture_id": "optional_cli_pack",
                        "fixture_kind": "optional_provider_comparison_pack",
                        "bundle_dir": os.path.relpath(REPRESENTATIVE_FIXTURE_BUNDLE_DIR, start=pack_dir),
                        "vector_fixture": os.path.relpath(REPRESENTATIVE_VECTOR_FIXTURE_PATH, start=pack_dir),
                        "metadata": {
                            "origin": "sanitized Chronicle-derived fixture pack",
                            "sanitization_status": "sanitized",
                            "intended_test_scope": ["cli_registry"],
                        },
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    result = _run_cli(
        "list-fixtures",
        "--json",
        "--locale",
        "en",
        "--no-env-fixture-dirs",
        "--fixture-dir",
        str(pack_dir),
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["fixture_count"] == 3
    assert payload["fixtures"][-1]["fixture_id"] == "optional_cli_pack"
    assert payload["fixtures"][-1]["source_name"] == "cli_optional_pack"


def test_list_plugins_cli_returns_provider_plugin_registry():
    result = _run_cli("list-plugins", "--json", "--locale", "en")

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "plugins_loaded"
    assert payload["plugin_count"] == 3
    assert payload["plugins"][0]["plugin_name"] == "gemma4"
    assert payload["plugins"][1]["plugin_name"] == "openai-compatible-hosted"
    assert payload["plugins"][1]["metadata"]["hosting_mode"] == "hosted"
    assert payload["plugins"][2]["plugin_name"] == "static-test-provider"
    assert payload["plugins"][0]["available"] is False
    assert payload["plugins"][0]["metadata"]["hosting_mode"] == "local"
    assert payload["plugins"][0]["metadata"]["supports_answer_generation"] is True
    assert payload["plugins"][2]["metadata"]["supports_answer_generation"] is False


def test_doctor_plugin_cli_reports_missing_and_present_env_vars():
    result = _run_cli(
        "doctor-plugin",
        "gemma4",
        "--json",
        "--locale",
        "en",
        env={
            "GEMMA4_ENABLED": "true",
            "GEMMA4_BASE_URL": "http://127.0.0.1:11434",
            "GEMMA4_MODEL": "gemma4",
            "GEMMA4_API_KEY": "secret-token",
        },
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "plugin_diagnosed"
    assert payload["plugin_name"] == "gemma4"
    assert payload["available"] is True
    assert payload["missing_required_env_vars"] == []
    assert payload["metadata"]["hosting_mode"] == "local"
    assert payload["env_checks"][0]["value_preview"] == "true"
    assert payload["env_checks"][1]["value_preview"] == "http://127.0.0.1:11434"
    assert payload["env_checks"][3]["value_preview"] == "(unset)"
    assert payload["env_checks"][4]["value_preview"] == "<redacted>"


def test_doctor_plugin_cli_reports_missing_required_env_vars_for_hosted_plugin():
    result = _run_cli(
        "doctor-plugin",
        "openai-compatible-hosted",
        "--json",
        "--locale",
        "en",
        env={
            "OPENAI_COMPATIBLE_HOSTED_ENABLED": "true",
        },
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["plugin_name"] == "openai-compatible-hosted"
    assert payload["available"] is False
    assert payload["availability_reason"] == "missing required env var: OPENAI_COMPATIBLE_HOSTED_BASE_URL"
    assert payload["missing_required_env_vars"] == [
        "OPENAI_COMPATIBLE_HOSTED_BASE_URL",
        "OPENAI_COMPATIBLE_HOSTED_MODEL",
        "OPENAI_COMPATIBLE_HOSTED_API_KEY",
    ]


def test_run_query_cli_accepts_gemma4_answer_plugin(tmp_path: Path):
    output_path = tmp_path / "artifact.json"
    server = _start_json_server(
        response_body={
            "choices": [
                {
                    "message": {
                        "content": "gemma4 local answer",
                    }
                }
            ]
        }
    )

    try:
        result = _run_cli(
            "run-query",
            str(FIXTURE_BUNDLE_DIR),
            "--query",
            "fixture bundle",
            "--mode",
            "graph",
            "--answer-plugin",
            "gemma4",
            "--output",
            str(output_path),
            "--json",
            "--locale",
            "en",
            env={
                "GEMMA4_ENABLED": "true",
                "GEMMA4_BASE_URL": server.base_url,
                "GEMMA4_MODEL": "gemma4",
            },
        )
    finally:
        server.shutdown()
        server.thread.join(timeout=5)
        server.server_close()

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["answer_plugin"] == "gemma4"
    assert payload["answer_text"] == "gemma4 local answer"
    assert payload["metadata"]["answer_generator"] == "gemma4"
    assert output_path.exists()


def test_run_query_cli_returns_error_when_gemma4_plugin_is_not_configured():
    result = _run_cli(
        "run-query",
        str(FIXTURE_BUNDLE_DIR),
        "--query",
        "fixture bundle",
        "--mode",
        "graph",
        "--answer-plugin",
        "gemma4",
        "--json",
        "--locale",
        "en",
        env={
            "GEMMA4_ENABLED": "false",
        },
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["status"] == "error"
    assert payload["error_category"] == "provider_plugin"
    assert "GEMMA4_ENABLED is not enabled" in payload["error"]


def test_compare_query_runs_cli_compares_baseline_with_hosted_plugin(tmp_path: Path):
    baseline_output = tmp_path / "baseline.json"
    plugin_output = tmp_path / "plugin.json"
    server = _start_json_server(
        response_body={
            "choices": [
                {
                    "message": {
                        "content": "hosted provider answer",
                    }
                }
            ]
        }
    )

    try:
        result = _run_cli(
            "compare-query-runs",
            str(FIXTURE_BUNDLE_DIR),
            "--query",
            "fixture bundle",
            "--mode",
            "graph",
            "--answer-plugin",
            "openai-compatible-hosted",
            "--baseline-output",
            str(baseline_output),
            "--plugin-output",
            str(plugin_output),
            "--json",
            "--locale",
            "en",
            env={
                "OPENAI_COMPATIBLE_HOSTED_ENABLED": "true",
                "OPENAI_COMPATIBLE_HOSTED_BASE_URL": server.base_url,
                "OPENAI_COMPATIBLE_HOSTED_MODEL": "hosted-model",
                "OPENAI_COMPATIBLE_HOSTED_API_KEY": "hosted-key",
            },
        )
    finally:
        server.shutdown()
        server.thread.join(timeout=5)
        server.server_close()

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "comparative_evaluation_completed"
    assert payload["answer_plugin"] == "openai-compatible-hosted"
    assert payload["baseline"]["metadata"]["answer_generator"] == "deterministic_baseline"
    assert payload["plugin"]["metadata"]["answer_generator"] == "openai-compatible-hosted"
    assert payload["comparison"]["answer_text_changed"] is True
    assert "answer_text_changed" in payload["comparison_summary"]["changed_fields"]
    assert baseline_output.exists()
    assert plugin_output.exists()


class _JsonHandler(BaseHTTPRequestHandler):
    response_body = b"{}"

    def do_POST(self):  # noqa: N802
        content_length = int(self.headers.get("Content-Length", "0"))
        _ = self.rfile.read(content_length)
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(self.response_body)

    def log_message(self, format, *args):  # noqa: A003
        return


class _ServerHandle:
    def __init__(self, httpd: ThreadingHTTPServer, thread: threading.Thread) -> None:
        self.httpd = httpd
        self.thread = thread
        self.base_url = f"http://127.0.0.1:{httpd.server_address[1]}"

    def shutdown(self) -> None:
        self.httpd.shutdown()

    def server_close(self) -> None:
        self.httpd.server_close()


def _start_json_server(*, response_body: dict[str, object]) -> _ServerHandle:
    handler = type(
        "TestJsonHandler",
        (_JsonHandler,),
        {"response_body": json.dumps(response_body).encode("utf-8")},
    )
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return _ServerHandle(httpd=httpd, thread=thread)


def test_run_query_cli_can_write_artifact(tmp_path: Path):
    output_path = tmp_path / "artifact.json"

    result = _run_cli(
        "run-query",
        str(FIXTURE_BUNDLE_DIR),
        "--query",
        "fixture bundle",
        "--mode",
        "graph",
        "--output",
        str(output_path),
        "--json",
        "--locale",
        "en",
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "executed"
    assert payload["runtime_status"] == "answered"
    assert payload["artifact"]["bundle_summary"]["bundle_kind"] == "query_engine_handoff_bundle"
    assert payload["chronicle_trial_alignment"]["record_kind"] == "query_engine_bundle_trial"
    assert output_path.exists()


def test_validate_bundle_cli_returns_error_for_missing_bundle(tmp_path: Path):
    missing_dir = tmp_path / "missing"

    result = _run_cli("validate-bundle", str(missing_dir), "--json", "--locale", "en")

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["status"] == "error"
    assert payload["error_code"] == "bundle_validation.missing_required_file"
    assert payload["error_category"] == "bundle_validation"


def test_validate_bundle_cli_uses_locale_environment_fallback():
    result = _run_cli(
        "validate-bundle",
        str(FIXTURE_BUNDLE_DIR),
        "--json",
        env={"CHRONICLE_EXTERNAL_QUERY_LOCALE": "en"},
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["summary"] == "Bundle validated successfully."


def test_show_artifact_cli_reads_saved_artifact(tmp_path: Path):
    artifact_path = tmp_path / "artifact.json"
    create_result = _run_cli(
        "run-query",
        str(FIXTURE_BUNDLE_DIR),
        "--query",
        "fixture bundle",
        "--mode",
        "graph",
        "--output",
        str(artifact_path),
        "--json",
        "--locale",
        "en",
    )
    assert create_result.returncode == 0

    result = _run_cli("show-artifact", str(artifact_path), "--json", "--locale", "en")

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "artifact_loaded"
    assert payload["query"] == "fixture bundle"
    assert payload["match_count"] >= 1
    assert payload["source_match_counts"]["graph"] >= 1
    assert payload["overlap_source_record_ids"] == []
    assert payload["bundle_summary"]["bundle_kind"] == "query_engine_handoff_bundle"
    assert payload["chronicle_trial_alignment"]["record_kind"] == "query_engine_bundle_trial"


def test_show_artifact_cli_returns_json_error_for_invalid_artifact(tmp_path: Path):
    artifact_path = tmp_path / "invalid-artifact.json"
    artifact_path.write_text("{invalid json", encoding="utf-8")

    result = _run_cli("show-artifact", str(artifact_path), "--json", "--locale", "en")

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["status"] == "error"
    assert payload["summary"] == "Evaluation artifact loading failed."
    assert payload["error_code"] == "evaluation_artifact_validation.invalid_artifact"
    assert payload["error_category"] == "evaluation_artifact_validation"
    assert "evaluation artifact contains invalid JSON" in payload["error"]


def test_compare_artifacts_cli_reports_deltas(tmp_path: Path):
    answered_path = tmp_path / "answered.json"
    insufficient_path = tmp_path / "insufficient.json"
    answered = _run_cli(
        "run-query",
        str(FIXTURE_BUNDLE_DIR),
        "--query",
        "fixture bundle",
        "--mode",
        "graph",
        "--output",
        str(answered_path),
        "--json",
        "--locale",
        "en",
    )
    assert answered.returncode == 0
    insufficient = _run_cli(
        "run-query",
        str(FIXTURE_BUNDLE_DIR),
        "--query",
        "nonexistent lookup",
        "--mode",
        "graph",
        "--output",
        str(insufficient_path),
        "--json",
        "--locale",
        "en",
    )
    assert insufficient.returncode == 0

    result = _run_cli(
        "compare-artifacts",
        str(answered_path),
        str(insufficient_path),
        "--json",
        "--locale",
        "en",
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "artifacts_compared"
    assert "runtime_status_changed" in payload["comparison_summary"]["changed_fields"]
    assert payload["comparison"]["runtime_status_changed"] is True
    assert payload["comparison"]["sufficiency_changed"] is True
    assert payload["comparison_summary"]["difference_count"] >= 1
    assert payload["comparison_summary"]["query_matches"] is False
    assert payload["comparison"]["bundle_kind_changed"] is False
    assert payload["comparison"]["contract_versions_changed"] is False


def test_compare_artifacts_cli_returns_json_error_for_invalid_artifact(tmp_path: Path):
    left_artifact_path = tmp_path / "left-artifact.json"
    right_artifact_path = tmp_path / "right-artifact.json"
    left_artifact_path.write_text("{invalid json", encoding="utf-8")
    right_artifact_path.write_text("{invalid json", encoding="utf-8")

    result = _run_cli(
        "compare-artifacts",
        str(left_artifact_path),
        str(right_artifact_path),
        "--json",
        "--locale",
        "en",
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["status"] == "error"
    assert payload["summary"] == "Evaluation artifact comparison failed."
    assert payload["error_code"] == "evaluation_artifact_validation.invalid_artifact"
    assert payload["error_category"] == "evaluation_artifact_validation"
    assert "evaluation artifact contains invalid JSON" in payload["error"]


def test_render_artifact_report_cli_writes_markdown(tmp_path: Path):
    artifact_path = tmp_path / "artifact.json"
    report_path = tmp_path / "report.md"
    create_result = _run_cli(
        "run-query",
        str(FIXTURE_BUNDLE_DIR),
        "--query",
        "fixture bundle",
        "--mode",
        "graph",
        "--output",
        str(artifact_path),
        "--json",
        "--locale",
        "en",
    )
    assert create_result.returncode == 0

    result = _run_cli(
        "render-artifact-report",
        str(artifact_path),
        "--output",
        str(report_path),
        "--json",
        "--locale",
        "en",
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "report_rendered"
    assert payload["runtime_status"] == "answered"
    assert payload["retrieval_mode"] == "graph-only"
    assert payload["match_count"] >= 1
    assert payload["markdown_line_count"] >= 1
    assert "# Query-Engine Handoff Bundle Trial Report" in payload["markdown"]
    assert report_path.exists()


def test_render_artifact_report_cli_returns_json_error_for_invalid_artifact(tmp_path: Path):
    artifact_path = tmp_path / "invalid-artifact.json"
    artifact_path.write_text("{invalid json", encoding="utf-8")

    result = _run_cli(
        "render-artifact-report",
        str(artifact_path),
        "--json",
        "--locale",
        "en",
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["status"] == "error"
    assert payload["summary"] == "Markdown trial report rendering failed."
    assert "evaluation artifact contains invalid JSON" in payload["error"]


def test_render_comparison_report_cli_writes_markdown(tmp_path: Path):
    left_artifact_path = tmp_path / "left-artifact.json"
    right_artifact_path = tmp_path / "right-artifact.json"
    report_path = tmp_path / "comparison-report.md"
    left_result = _run_cli(
        "run-query",
        str(FIXTURE_BUNDLE_DIR),
        "--query",
        "nonexistent lookup",
        "--mode",
        "graph",
        "--output",
        str(left_artifact_path),
        "--json",
        "--locale",
        "en",
    )
    assert left_result.returncode == 0
    right_result = _run_cli(
        "run-query",
        str(FIXTURE_BUNDLE_DIR),
        "--query",
        "fixture bundle",
        "--mode",
        "graph",
        "--output",
        str(right_artifact_path),
        "--json",
        "--locale",
        "en",
    )
    assert right_result.returncode == 0

    result = _run_cli(
        "render-comparison-report",
        str(left_artifact_path),
        str(right_artifact_path),
        "--output",
        str(report_path),
        "--json",
        "--locale",
        "en",
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "comparison_report_rendered"
    assert payload["comparison_summary"]["runtime_status_changed"] is True
    assert payload["comparison_summary"]["bundle_summary_changed"] is False
    assert payload["markdown_line_count"] >= 1
    assert "# Query-Engine Handoff Bundle Comparison Report" in payload["markdown"]
    assert report_path.exists()


def test_render_comparison_report_cli_returns_json_error_for_invalid_artifact(tmp_path: Path):
    left_artifact_path = tmp_path / "left-artifact.json"
    right_artifact_path = tmp_path / "right-artifact.json"
    left_artifact_path.write_text(
        json.dumps({"artifact_version": "1.0", "query": "fixture bundle"}, ensure_ascii=False),
        encoding="utf-8",
    )
    right_artifact_path.write_text(
        json.dumps({"artifact_version": "1.0", "query": "fixture bundle"}, ensure_ascii=False),
        encoding="utf-8",
    )

    result = _run_cli(
        "render-comparison-report",
        str(left_artifact_path),
        str(right_artifact_path),
        "--json",
        "--locale",
        "en",
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["status"] == "error"
    assert payload["summary"] == "Markdown comparison report rendering failed."
    assert "evaluation artifact is missing required keys" in payload["error"]


def test_run_query_cli_accepts_vector_fixture_for_hybrid_mode(tmp_path: Path):
    artifact_path = tmp_path / "hybrid-artifact.json"

    result = _run_cli(
        "run-query",
        str(FIXTURE_BUNDLE_DIR),
        "--query",
        "fixture vector",
        "--mode",
        "hybrid",
        "--vector-fixture",
        str(VECTOR_FIXTURE_PATH),
        "--output",
        str(artifact_path),
        "--json",
        "--locale",
        "en",
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["mode"] == "hybrid"
    assert payload["vector_fixture"] == str(VECTOR_FIXTURE_PATH)
    assert payload["match_count"] >= 2
    assert artifact_path.exists()


def test_run_query_cli_returns_json_error_for_invalid_vector_fixture(tmp_path: Path):
    invalid_fixture_path = tmp_path / "invalid-vector-fixture.json"
    invalid_fixture_path.write_text('{"identifier": "v_evt_1"}', encoding="utf-8")

    result = _run_cli(
        "run-query",
        str(FIXTURE_BUNDLE_DIR),
        "--query",
        "fixture vector",
        "--mode",
        "hybrid",
        "--vector-fixture",
        str(invalid_fixture_path),
        "--json",
        "--locale",
        "en",
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["status"] == "error"
    assert payload["summary"] == "Query execution failed."
    assert "vector fixture must decode to a list" in payload["error"]


def test_run_query_cli_representative_hybrid_artifact_is_repeatably_comparable(tmp_path: Path):
    first_artifact_path = tmp_path / "first-representative-artifact.json"
    second_artifact_path = tmp_path / "second-representative-artifact.json"

    first = _run_cli(
        "run-query",
        str(REPRESENTATIVE_FIXTURE_BUNDLE_DIR),
        "--query",
        "release planning follow-up context",
        "--mode",
        "hybrid",
        "--vector-fixture",
        str(REPRESENTATIVE_VECTOR_FIXTURE_PATH),
        "--output",
        str(first_artifact_path),
        "--json",
        "--locale",
        "en",
    )
    second = _run_cli(
        "run-query",
        str(REPRESENTATIVE_FIXTURE_BUNDLE_DIR),
        "--query",
        "release planning follow-up context",
        "--mode",
        "hybrid",
        "--vector-fixture",
        str(REPRESENTATIVE_VECTOR_FIXTURE_PATH),
        "--output",
        str(second_artifact_path),
        "--json",
        "--locale",
        "en",
    )

    assert first.returncode == 0
    assert second.returncode == 0

    comparison = _run_cli(
        "compare-artifacts",
        str(first_artifact_path),
        str(second_artifact_path),
        "--json",
        "--locale",
        "en",
    )

    assert comparison.returncode == 0
    payload = json.loads(comparison.stdout)
    assert payload["comparison_summary"]["difference_count"] == 0
    assert payload["comparison"]["runtime_status_changed"] is False
    assert payload["comparison"]["retrieval_mode_changed"] is False
    assert payload["comparison"]["contract_versions_changed"] is False
