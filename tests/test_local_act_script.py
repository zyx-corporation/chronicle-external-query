from __future__ import annotations

import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "run_local_act.sh"


def _write_executable(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)


def test_run_local_act_doctor_reports_expected_tools(tmp_path: Path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()

    act_path = bin_dir / "act"
    docker_path = bin_dir / "docker"
    credential_path = bin_dir / "docker-credential-desktop"

    _write_executable(
        act_path,
        "#!/usr/bin/env bash\n"
        "if [[ \"${1:-}\" == \"--version\" ]]; then\n"
        "  echo 'act version fake-test'\n"
        "  exit 0\n"
        "fi\n"
        "echo unexpected act invocation >&2\n"
        "exit 1\n",
    )
    _write_executable(
        docker_path,
        "#!/usr/bin/env bash\n"
        "if [[ \"${1:-}\" == \"--version\" ]]; then\n"
        "  echo 'Docker version fake-test'\n"
        "  exit 0\n"
        "fi\n"
        "echo unexpected docker invocation >&2\n"
        "exit 1\n",
    )
    _write_executable(
        credential_path,
        "#!/usr/bin/env bash\n"
        "exit 0\n",
    )

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    env["ACT_BIN"] = str(act_path)
    env["DOCKER_DESKTOP_BIN"] = str(bin_dir)

    result = subprocess.run(
        ["bash", str(SCRIPT_PATH), "doctor"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0
    assert f"act_bin={act_path}" in result.stdout
    assert "act version fake-test" in result.stdout
    assert f"docker_bin={docker_path}" in result.stdout
    assert "Docker version fake-test" in result.stdout
    assert f"docker_credential_helper={credential_path}" in result.stdout
    assert "release-dispatch.event.json" in result.stdout


def test_run_local_act_all_invokes_ci_then_release_notes_only(tmp_path: Path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()

    act_path = bin_dir / "act"
    docker_path = bin_dir / "docker"
    credential_path = bin_dir / "docker-credential-desktop"
    act_log = tmp_path / "act.log"

    _write_executable(
        act_path,
        "#!/usr/bin/env bash\n"
        "if [[ \"${1:-}\" == \"--version\" ]]; then\n"
        "  echo 'act version fake-test'\n"
        "  exit 0\n"
        "fi\n"
        "printf '%s\\n' \"$*\" >> \"" + str(act_log) + "\"\n",
    )
    _write_executable(
        docker_path,
        "#!/usr/bin/env bash\n"
        "if [[ \"${1:-}\" == \"--version\" ]]; then\n"
        "  echo 'Docker version fake-test'\n"
        "  exit 0\n"
        "fi\n"
        "exit 0\n",
    )
    _write_executable(
        credential_path,
        "#!/usr/bin/env bash\n"
        "exit 0\n",
    )

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    env["ACT_BIN"] = str(act_path)
    env["DOCKER_DESKTOP_BIN"] = str(bin_dir)

    result = subprocess.run(
        ["bash", str(SCRIPT_PATH), "all"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0

    act_calls = act_log.read_text(encoding="utf-8").splitlines()
    assert len(act_calls) == 2
    assert act_calls[0].endswith("-W /Users/tomyuk/Projects/Chronicle/chronicle-external-query/.github/workflows/ci.yml -j test")
    assert "workflow_dispatch" in act_calls[1]
    assert "-j build-release-notes" in act_calls[1]
    assert "-j verify" not in act_calls[1]


def test_run_local_act_release_publish_is_rejected():
    env = os.environ.copy()
    env["ACT_BIN"] = "/usr/bin/true"

    result = subprocess.run(
        ["bash", str(SCRIPT_PATH), "release-publish"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 2
    assert "not supported under local act" in result.stderr


def test_run_local_act_ci_accepts_extra_args_from_env_and_cli(tmp_path: Path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()

    act_path = bin_dir / "act"
    act_log = tmp_path / "act.log"

    _write_executable(
        act_path,
        "#!/usr/bin/env bash\n"
        "printf '%s\\n' \"$*\" >> \"" + str(act_log) + "\"\n",
    )

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    env["ACT_BIN"] = str(act_path)
    env["ACT_ARGS"] = "--pull=false --verbose"

    result = subprocess.run(
        ["bash", str(SCRIPT_PATH), "ci", "--", "--artifact-server-path", "/tmp/act-artifacts"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0
    act_calls = act_log.read_text(encoding="utf-8").splitlines()
    assert len(act_calls) == 1
    assert act_calls[0].startswith("--pull=false --verbose --artifact-server-path /tmp/act-artifacts ")
    assert act_calls[0].endswith("-W /Users/tomyuk/Projects/Chronicle/chronicle-external-query/.github/workflows/ci.yml -j test")


def test_run_local_act_release_verify_optional_uses_optional_event_file(tmp_path: Path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()

    act_path = bin_dir / "act"
    act_log = tmp_path / "act.log"

    _write_executable(
        act_path,
        "#!/usr/bin/env bash\n"
        "printf '%s\\n' \"$*\" >> \"" + str(act_log) + "\"\n",
    )

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    env["ACT_BIN"] = str(act_path)

    result = subprocess.run(
        ["bash", str(SCRIPT_PATH), "release-verify-optional"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0
    act_calls = act_log.read_text(encoding="utf-8").splitlines()
    assert len(act_calls) == 1
    assert ".github/act/release-dispatch.optional-plugins.event.json" in act_calls[0]
    assert act_calls[0].endswith("-j verify")
