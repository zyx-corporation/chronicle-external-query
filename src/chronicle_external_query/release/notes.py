from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ReleaseNotesContext:
    version: str
    release_date: str
    plugin_registry_summary: str
    roadmap_summary: list[str]


def build_release_notes(*, version: str, release_date: str, repo_root: Path) -> str:
    context = ReleaseNotesContext(
        version=version,
        release_date=release_date,
        plugin_registry_summary=_plugin_registry_summary(repo_root),
        roadmap_summary=_roadmap_summary(repo_root),
    )
    roadmap_lines = "\n".join(f"- {line}" for line in context.roadmap_summary)
    return "\n".join(
        [
            f"# {context.version}",
            "",
            f"Release date: {context.release_date}",
            "",
            "## Supported Boundary",
            "",
            "- deterministic local smoke remains the primary release gate",
            "- provider-backed paths remain opt-in and non-blocking for the baseline release",
            "- Chronicle primary records remain authoritative and unchanged",
            "",
            "## Automation Summary",
            "",
            "- release workflow builds artifacts, runs release-candidate gating, and can publish a GitHub release",
            f"- plugin compatibility matrix status: {context.plugin_registry_summary}",
            "",
            "## Roadmap Snapshot",
            "",
            roadmap_lines,
            "",
            "## Release Evidence",
            "",
            "- `bash scripts/smoke_clean_checkout.sh` remains the baseline release gate",
            "- optional plugin compatibility is reported separately and does not block the baseline unless explicitly required",
            "- release notes are generated from repository-resident roadmap and release automation context",
        ]
    )


def _plugin_registry_summary(repo_root: Path) -> str:
    loader_path = repo_root / "src" / "chronicle_external_query" / "plugins" / "loader.py"
    text = loader_path.read_text(encoding="utf-8")
    plugins = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith('"') and 'chronicle_external_query.plugins.providers.' in stripped:
            plugins.append(stripped.split('"')[1])
    return ", ".join(plugins)


def _roadmap_summary(repo_root: Path) -> list[str]:
    roadmap_path = repo_root / "docs" / "extension-roadmap.md"
    lines = roadmap_path.read_text(encoding="utf-8").splitlines()
    summary: list[str] = []
    current_heading = ""
    pending_status = False
    for line in lines:
        if line.startswith("## Milestone "):
            current_heading = line.replace("## ", "").strip()
            pending_status = False
        elif line.strip().startswith("Status:") and current_heading:
            pending_status = True
        elif pending_status and line.strip():
            summary.append(f"{current_heading} - {line.strip()}")
            pending_status = False
    return summary
