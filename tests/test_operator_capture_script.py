from __future__ import annotations

import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "operator_capture.sh"


def test_operator_capture_help_includes_expected_sections():
    result = subprocess.run(
        ["bash", str(SCRIPT_PATH), "--help"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "captures bundle summary JSON" in result.stdout
    assert "OUTPUT_DIR" in result.stdout
    assert "VENV_DIR" in result.stdout


def test_operator_capture_dry_run_prints_expected_commands(tmp_path: Path):
    venv_bin = tmp_path / "venv" / "bin"
    venv_bin.mkdir(parents=True)
    cli_path = venv_bin / "chronicle-external-query"
    cli_path.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    cli_path.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{venv_bin}:{env['PATH']}"
    env["DRY_RUN"] = "1"
    env["VENV_DIR"] = str(tmp_path / "venv")
    result = subprocess.run(
        [
            "bash",
            str(SCRIPT_PATH),
            "tests/fixtures/query_engine_bundle/representative_cli_bundle",
            str(tmp_path / "capture"),
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0
    assert "validate-bundle tests/fixtures/query_engine_bundle/representative_cli_bundle --json" in result.stdout
    assert "show-bundle tests/fixtures/query_engine_bundle/representative_cli_bundle --json" in result.stdout
    assert "--output" in result.stdout
    assert "render-artifact-report" in result.stdout
    assert "> " in result.stdout


def test_operator_capture_non_dry_run_writes_outputs_once_each(tmp_path: Path):
    venv_bin = tmp_path / "venv" / "bin"
    venv_bin.mkdir(parents=True)
    log_path = tmp_path / "capture-log.txt"
    cli_path = venv_bin / "chronicle-external-query"
    cli_path.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        f"LOG_PATH={str(log_path)!r}\n"
        "printf '%s\\n' \"$*\" >> \"$LOG_PATH\"\n"
        "if [ \"$1\" = \"run-query\" ]; then\n"
        "  shift\n"
        "  while [ \"$#\" -gt 0 ]; do\n"
        "    if [ \"$1\" = \"--output\" ]; then\n"
        "      printf '{\"artifact\":\"ok\"}\\n' > \"$2\"\n"
        "      break\n"
        "    fi\n"
        "    shift\n"
        "  done\n"
        "  printf '{\"status\":\"query\"}\\n'\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1\" = \"render-artifact-report\" ]; then\n"
        "  shift\n"
        "  while [ \"$#\" -gt 0 ]; do\n"
        "    if [ \"$1\" = \"--output\" ]; then\n"
        "      printf '# report\\n' > \"$2\"\n"
        "      break\n"
        "    fi\n"
        "    shift\n"
        "  done\n"
        "  printf '{\"status\":\"report\"}\\n'\n"
        "  exit 0\n"
        "fi\n"
        "printf '{\"status\":\"ok\"}\\n'\n",
        encoding="utf-8",
    )
    cli_path.chmod(0o755)

    output_dir = tmp_path / "capture"
    env = os.environ.copy()
    env["VENV_DIR"] = str(tmp_path / "venv")

    result = subprocess.run(
        [
            "bash",
            str(SCRIPT_PATH),
            "tests/fixtures/query_engine_bundle/representative_cli_bundle",
            str(output_dir),
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0
    assert result.stdout.strip() == str(output_dir)
    assert (output_dir / "validate-bundle.json").read_text(encoding="utf-8") == '{"status":"ok"}\n'
    assert (output_dir / "show-bundle.json").read_text(encoding="utf-8") == '{"status":"ok"}\n'
    assert (output_dir / "trial-artifact.json").read_text(encoding="utf-8") == '{"artifact":"ok"}\n'
    assert (output_dir / "run-query.json").read_text(encoding="utf-8") == '{"status":"query"}\n'
    assert (output_dir / "trial-report.md").read_text(encoding="utf-8") == "# report\n"
    assert (output_dir / "render-artifact-report.json").read_text(encoding="utf-8") == '{"status":"report"}\n'
    assert log_path.read_text(encoding="utf-8").splitlines() == [
        "validate-bundle tests/fixtures/query_engine_bundle/representative_cli_bundle --json",
        "show-bundle tests/fixtures/query_engine_bundle/representative_cli_bundle --json",
        "run-query tests/fixtures/query_engine_bundle/representative_cli_bundle --query release planning follow-up context --mode hybrid --vector-fixture tests/fixtures/vector_matches/representative-vector-matches.json --output "
        f"{output_dir / 'trial-artifact.json'} --json",
        "render-artifact-report "
        f"{output_dir / 'trial-artifact.json'} --output {output_dir / 'trial-report.md'} --json",
    ]
