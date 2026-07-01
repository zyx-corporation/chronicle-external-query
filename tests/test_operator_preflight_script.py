from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "operator_preflight.sh"


def test_operator_preflight_help_includes_expected_sections():
    result = subprocess.run(
        ["bash", str(SCRIPT_PATH), "--help"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "ensures a local .venv exists" in result.stdout
    assert "BUNDLE_DIR" in result.stdout
    assert "REPORT_PATH" in result.stdout


def test_operator_preflight_dry_run_prints_expected_commands():
    venv_dir = "/tmp/test-operator-preflight-venv"
    result = subprocess.run(
        ["bash", str(SCRIPT_PATH)],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env={
            "PATH": "/usr/bin:/bin:/opt/homebrew/bin",
            "PYTHON_BIN": "/usr/bin/python3",
            "DRY_RUN": "1",
            "VENV_DIR": venv_dir,
            "ARTIFACT_PATH": "/tmp/test-operator-preflight-artifact.json",
            "REPORT_PATH": "/tmp/test-operator-preflight-report.md",
        },
    )

    assert result.returncode == 0
    assert f"/usr/bin/python3 -m venv {venv_dir}" in result.stdout
    assert "pip install -e" in result.stdout
    assert "pytest -q" in result.stdout
    assert "chronicle-external-query validate-bundle tests/fixtures/query_engine_bundle/representative_cli_bundle --json" in result.stdout
    assert "--mode hybrid" in result.stdout
    assert "render-artifact-report /tmp/test-operator-preflight-artifact.json" in result.stdout
