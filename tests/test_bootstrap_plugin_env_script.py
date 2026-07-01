from __future__ import annotations

import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_SCRIPT_PATH = REPO_ROOT / "scripts" / "bootstrap_plugin_env.sh"


def _write_executable(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)


def _prepare_script_repo(tmp_path: Path) -> tuple[Path, Path]:
    repo_dir = tmp_path / "repo"
    scripts_dir = repo_dir / "scripts"
    scripts_dir.mkdir(parents=True)
    script_path = scripts_dir / "bootstrap_plugin_env.sh"
    script_path.write_text(SOURCE_SCRIPT_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    script_path.chmod(0o755)
    return repo_dir, script_path


def test_bootstrap_plugin_env_writes_local_plugin_env_file(tmp_path: Path):
    repo_dir, script_path = _prepare_script_repo(tmp_path)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()

    curl_path = bin_dir / "curl"
    _write_executable(
        curl_path,
        "#!/usr/bin/env bash\n"
        "printf '%s' '{\"object\":\"list\",\"data\":[{\"id\":\"gemma4:26b\"},{\"id\":\"other-model\"}]}'\n",
    )

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"

    result = subprocess.run(
        ["bash", str(script_path), "--force"],
        cwd=repo_dir,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0
    output_file = repo_dir / ".env.local.plugins"
    assert output_file.exists()
    payload = output_file.read_text(encoding="utf-8")
    assert "export GEMMA4_ENABLED=true" in payload
    assert "export GEMMA4_BASE_URL=http://127.0.0.1:11434" in payload
    assert "export GEMMA4_MODEL=gemma4:26b" in payload
    assert "export OPENAI_COMPATIBLE_HOSTED_BASE_URL=https://api.openai.com" in payload
    assert "Wrote " in result.stdout
    assert ".venv/bin/chronicle-external-query doctor-plugin gemma4 --json" in result.stdout


def test_bootstrap_plugin_env_refuses_to_overwrite_without_force(tmp_path: Path):
    repo_dir, script_path = _prepare_script_repo(tmp_path)
    existing_file = repo_dir / ".env.local.plugins"
    existing_file.write_text("export GEMMA4_MODEL=keep-me\n", encoding="utf-8")

    result = subprocess.run(
        ["bash", str(script_path)],
        cwd=repo_dir,
        check=False,
        capture_output=True,
        text=True,
        env=os.environ.copy(),
    )

    assert result.returncode == 1
    assert "already exists" in result.stderr
    assert existing_file.read_text(encoding="utf-8") == "export GEMMA4_MODEL=keep-me\n"
