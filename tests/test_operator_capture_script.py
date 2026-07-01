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


def test_operator_capture_dry_run_prints_expected_commands(tmp_path: Path):
    venv_bin = tmp_path / "venv" / "bin"
    venv_bin.mkdir(parents=True)
    cli_path = venv_bin / "chronicle-external-query"
    cli_path.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    cli_path.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{venv_bin}:{env['PATH']}"
    env["DRY_RUN"] = "1"

    env["DRY_RUN"] = "1"
    result = subprocess.run(
        [
            "bash",
            "-c",
            f'VENV_DIR="{tmp_path / "venv"}" bash "{SCRIPT_PATH}" tests/fixtures/query_engine_bundle/representative_cli_bundle "{tmp_path / "capture"}"',
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
