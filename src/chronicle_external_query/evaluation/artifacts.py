from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from chronicle_external_query.models import EvaluationArtifactValidationError
from chronicle_external_query.runtime.answer_runtime import RuntimeAnswer


@dataclass(frozen=True)
class EvaluationArtifact:
    artifact_version: str
    query: str
    runtime_status: str
    retrieval_mode: str
    answer_text: str
    sufficient: bool
    missing_behavior: str
    files_reviewed: list[str]
    reviewer: str
    downstream_consumer: str
    bundle_summary: dict[str, Any]
    metadata: dict[str, Any]
    provenance: dict[str, Any]
    matches: list[dict[str, Any]]


def build_evaluation_artifact(
    answer: RuntimeAnswer,
    *,
    artifact_version: str = "1.0",
    reviewer: str = "local-reviewer",
    downstream_consumer: str = "local-consumer",
    files_reviewed: list[str] | None = None,
    bundle_summary: dict[str, Any] | None = None,
) -> EvaluationArtifact:
    insufficiency_reasons = list(answer.provenance.insufficiency_reasons)
    sufficient = answer.status == "answered" and not insufficiency_reasons
    missing_behavior = "" if sufficient else _summarize_missing_behavior(insufficiency_reasons)
    return EvaluationArtifact(
        artifact_version=artifact_version,
        query=answer.query,
        runtime_status=answer.status,
        retrieval_mode=answer.provenance.retrieval_mode,
        answer_text=answer.answer_text,
        sufficient=sufficient,
        missing_behavior=missing_behavior,
        files_reviewed=files_reviewed or ["query_engine_handoff.json", "graph.json"],
        reviewer=reviewer,
        downstream_consumer=downstream_consumer,
        bundle_summary=bundle_summary or {},
        metadata=answer.metadata,
        provenance={
            "query": answer.provenance.query,
            "retrieval_mode": answer.provenance.retrieval_mode,
            "sources": list(answer.provenance.sources),
            "match_count": answer.provenance.match_count,
            "graph_node_count": answer.provenance.graph_node_count,
            "graph_edge_count": answer.provenance.graph_edge_count,
            "source_match_counts": answer.provenance.source_match_counts,
            "overlap_source_record_ids": list(answer.provenance.overlap_source_record_ids),
            "insufficiency_reasons": list(answer.provenance.insufficiency_reasons),
        },
        matches=[
            {
                "identifier": match.identifier,
                "source_record_id": match.source_record_id,
                "entity_type": match.entity_type,
                "title": match.title,
                "summary": match.summary,
                "score": match.score,
                "source": match.source,
                "matched_terms": list(match.matched_terms),
                "metadata": match.metadata,
            }
            for match in answer.graph_matches
        ],
    )


def save_evaluation_artifact(artifact: EvaluationArtifact, output_path: Path) -> None:
    output_path.write_text(json.dumps(_artifact_to_dict(artifact), ensure_ascii=False, indent=2), encoding="utf-8")


def load_evaluation_artifact(path: Path) -> EvaluationArtifact:
    if not path.exists():
        raise EvaluationArtifactValidationError(f"evaluation artifact file was not found: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise EvaluationArtifactValidationError(
            f"evaluation artifact contains invalid JSON: {path}"
        ) from exc
    if not isinstance(payload, dict):
        raise EvaluationArtifactValidationError("evaluation artifact must decode to an object")
    _require_artifact_keys(
        payload,
        {
            "artifact_version",
            "query",
            "runtime_status",
            "retrieval_mode",
            "answer_text",
            "sufficient",
        },
    )
    files_reviewed = payload.get("files_reviewed", [])
    bundle_summary = payload.get("bundle_summary", {})
    metadata = payload.get("metadata", {})
    provenance = payload.get("provenance", {})
    matches = payload.get("matches", [])
    _require_list_field(files_reviewed, field_name="files_reviewed")
    _require_dict_field(bundle_summary, field_name="bundle_summary")
    _require_dict_field(metadata, field_name="metadata")
    _require_dict_field(provenance, field_name="provenance")
    _require_list_field(matches, field_name="matches")
    _require_string_list_entries(files_reviewed, field_name="files_reviewed")
    _require_dict_list_entries(matches, field_name="matches")
    _require_match_entry_keys(matches)
    return EvaluationArtifact(
        artifact_version=str(payload["artifact_version"]),
        query=str(payload["query"]),
        runtime_status=str(payload["runtime_status"]),
        retrieval_mode=str(payload["retrieval_mode"]),
        answer_text=str(payload["answer_text"]),
        sufficient=bool(payload["sufficient"]),
        missing_behavior=str(payload.get("missing_behavior", "")),
        files_reviewed=[str(item) for item in files_reviewed],
        reviewer=str(payload.get("reviewer", "")),
        downstream_consumer=str(payload.get("downstream_consumer", "")),
        bundle_summary=dict(bundle_summary),
        metadata=dict(metadata),
        provenance=dict(provenance),
        matches=list(matches),
    )


def build_chronicle_trial_alignment(artifact: EvaluationArtifact) -> dict[str, Any]:
    return {
        "record_kind": "query_engine_bundle_trial",
        "query": artifact.query,
        "reviewer": artifact.reviewer,
        "downstream_consumer": artifact.downstream_consumer,
        "sufficient": artifact.sufficient,
        "missing_behavior": artifact.missing_behavior,
        "files_reviewed": artifact.files_reviewed,
        "bundle_summary": artifact.bundle_summary,
        "import_validation_status": artifact.metadata.get("status", artifact.runtime_status),
        "notes": [
            "local evaluation artifact is downstream-derived and non-authoritative",
            "Chronicle primary records remain authoritative over source record meaning",
        ],
    }


def render_markdown_trial_report(artifact: EvaluationArtifact) -> str:
    reviewed_lines = "\n".join(f"- [x] `{name}`" for name in artifact.files_reviewed) or "- [ ] `(none)`"
    contract_versions = artifact.bundle_summary.get("contract_versions", {})
    contract_version_lines = _render_contract_version_lines(contract_versions)
    overlap_source_record_ids = artifact.provenance.get("overlap_source_record_ids", [])
    overlap_summary = (
        ", ".join(f"`{record_id}`" for record_id in overlap_source_record_ids)
        if overlap_source_record_ids
        else "(none)"
    )
    source_match_counts = artifact.provenance.get("source_match_counts", {})
    source_count_summary = (
        ", ".join(f"{source}={count}" for source, count in source_match_counts.items())
        if source_match_counts
        else "(none)"
    )
    insufficiency_reasons = artifact.provenance.get("insufficiency_reasons", [])
    insufficiency_summary = (
        ", ".join(str(reason) for reason in insufficiency_reasons) if insufficiency_reasons else "(none)"
    )
    structural_findings = [
        f"- Import-validation status observed: {artifact.metadata.get('status', artifact.runtime_status)}",
        f"- Retrieval mode observed: {artifact.retrieval_mode}",
        f"- Match count observed: {len(artifact.matches)}",
        f"- Source match counts observed: {source_count_summary}",
        f"- Overlap source record ids observed: {overlap_summary}",
        f"- Insufficiency reasons observed: {insufficiency_summary}",
        "- Contract/version mismatches: compare against bundle_summary contract versions when reviewing drift",
        "- Missing files or parse errors: (none observed in local artifact)",
    ]
    if artifact.sufficient:
        sufficiency_lines = [
            "- [x] Bundle was sufficient for downstream trial",
            "- [ ] Bundle was insufficient for downstream trial",
            "- If insufficient, describe the missing behavior: (none)",
        ]
    else:
        sufficiency_lines = [
            "- [ ] Bundle was sufficient for downstream trial",
            "- [x] Bundle was insufficient for downstream trial",
            f"- If insufficient, describe the missing behavior: {artifact.missing_behavior or '(unspecified)'}",
        ]

    return "\n".join(
        [
            "# Query-Engine Handoff Bundle Trial Report",
            "",
            f"- Query: `{artifact.query}`",
            "- Trial date:",
            f"- Reviewer: {artifact.reviewer}",
            f"- Downstream consumer or repo: {artifact.downstream_consumer}",
            f"- Bundle kind: {artifact.bundle_summary.get('bundle_kind', '(unknown)')}",
            f"- Primary record path: {artifact.bundle_summary.get('primary_record_path', '(unknown)')}",
            (
                "- Graph stats: "
                f"{artifact.bundle_summary.get('graph_stats', {}).get('node_count', 0)} nodes / "
                f"{artifact.bundle_summary.get('graph_stats', {}).get('edge_count', 0)} edges"
            ),
            "",
            "## Bundle contract versions",
            "",
            *contract_version_lines,
            "",
            "## Files reviewed",
            "",
            reviewed_lines,
            "",
            "## Structural findings",
            "",
            *structural_findings,
            "",
            "## Sufficiency decision",
            "",
            *sufficiency_lines,
            "",
            "## Boundary confirmation",
            "",
            "- [x] Chronicle primary records remained authoritative",
            "- [x] No hosted query execution was expected from Chronicle Stack",
            "- [x] No downstream import execution was expected inside Chronicle Stack",
            "- [x] Any requested next step stays outside Chronicle Stack core",
        ]
    )


def render_markdown_comparison_report(
    left: EvaluationArtifact,
    right: EvaluationArtifact,
) -> str:
    comparison = compare_evaluation_artifacts(left, right)
    left_source_counts = _render_source_count_summary(left.provenance.get("source_match_counts", {}))
    right_source_counts = _render_source_count_summary(right.provenance.get("source_match_counts", {}))
    left_insufficiency = _render_reason_summary(left.provenance.get("insufficiency_reasons", []))
    right_insufficiency = _render_reason_summary(right.provenance.get("insufficiency_reasons", []))
    left_overlap = _render_record_id_summary(left.provenance.get("overlap_source_record_ids", []))
    right_overlap = _render_record_id_summary(right.provenance.get("overlap_source_record_ids", []))
    changed_lines = [
        f"- Runtime status changed: {comparison['runtime_status_changed']}",
        f"- Retrieval mode changed: {comparison['retrieval_mode_changed']}",
        f"- Sufficiency changed: {comparison['sufficiency_changed']}",
        f"- Match count delta: {comparison['match_count_delta']}",
        f"- Missing behavior changed: {comparison['missing_behavior_changed']}",
        f"- Bundle summary changed: {comparison['bundle_summary_changed']}",
        f"- Contract versions changed: {comparison['contract_versions_changed']}",
        f"- Graph stats changed: {comparison['graph_stats_changed']}",
    ]
    return "\n".join(
        [
            "# Query-Engine Handoff Bundle Comparison Report",
            "",
            "## Artifact inputs",
            "",
            f"- Left query: `{left.query}`",
            f"- Right query: `{right.query}`",
            f"- Left retrieval mode: {left.retrieval_mode}",
            f"- Right retrieval mode: {right.retrieval_mode}",
            f"- Left bundle kind: {left.bundle_summary.get('bundle_kind', '(unknown)')}",
            f"- Right bundle kind: {right.bundle_summary.get('bundle_kind', '(unknown)')}",
            "",
            "## Comparison summary",
            "",
            *changed_lines,
            "",
            "## Retrieval provenance",
            "",
            f"- Left source match counts: {left_source_counts}",
            f"- Right source match counts: {right_source_counts}",
            f"- Left overlap source record ids: {left_overlap}",
            f"- Right overlap source record ids: {right_overlap}",
            f"- Left insufficiency reasons: {left_insufficiency}",
            f"- Right insufficiency reasons: {right_insufficiency}",
            "",
            "## Bundle details",
            "",
            f"- Left primary record path: {comparison['left_bundle_summary'].get('primary_record_path', '(unknown)')}",
            f"- Right primary record path: {comparison['right_bundle_summary'].get('primary_record_path', '(unknown)')}",
            (
                "- Left graph stats: "
                f"{comparison['left_bundle_summary'].get('graph_stats', {}).get('node_count', 0)} nodes / "
                f"{comparison['left_bundle_summary'].get('graph_stats', {}).get('edge_count', 0)} edges"
            ),
            (
                "- Right graph stats: "
                f"{comparison['right_bundle_summary'].get('graph_stats', {}).get('node_count', 0)} nodes / "
                f"{comparison['right_bundle_summary'].get('graph_stats', {}).get('edge_count', 0)} edges"
            ),
        ]
    )


def compare_evaluation_artifacts(
    left: EvaluationArtifact,
    right: EvaluationArtifact,
) -> dict[str, Any]:
    left_bundle_summary = _normalized_bundle_summary(left)
    right_bundle_summary = _normalized_bundle_summary(right)
    return {
        "artifact_versions": [left.artifact_version, right.artifact_version],
        "query_matches": left.query == right.query,
        "runtime_status_changed": left.runtime_status != right.runtime_status,
        "retrieval_mode_changed": left.retrieval_mode != right.retrieval_mode,
        "sufficiency_changed": left.sufficient != right.sufficient,
        "match_count_delta": len(right.matches) - len(left.matches),
        "missing_behavior_changed": left.missing_behavior != right.missing_behavior,
        "insufficiency_changed": (
            left.provenance.get("insufficiency_reasons", [])
            != right.provenance.get("insufficiency_reasons", [])
        ),
        "bundle_summary_changed": left_bundle_summary != right_bundle_summary,
        "bundle_kind_changed": left_bundle_summary.get("bundle_kind") != right_bundle_summary.get("bundle_kind"),
        "primary_record_path_changed": (
            left_bundle_summary.get("primary_record_path")
            != right_bundle_summary.get("primary_record_path")
        ),
        "contract_versions_changed": (
            left_bundle_summary.get("contract_versions", {})
            != right_bundle_summary.get("contract_versions", {})
        ),
        "graph_stats_changed": (
            left_bundle_summary.get("graph_stats", {}) != right_bundle_summary.get("graph_stats", {})
        ),
        "left_bundle_summary": left_bundle_summary,
        "right_bundle_summary": right_bundle_summary,
    }


def _artifact_to_dict(artifact: EvaluationArtifact) -> dict[str, Any]:
    return {
        "artifact_version": artifact.artifact_version,
        "query": artifact.query,
        "runtime_status": artifact.runtime_status,
        "retrieval_mode": artifact.retrieval_mode,
        "answer_text": artifact.answer_text,
        "sufficient": artifact.sufficient,
        "missing_behavior": artifact.missing_behavior,
        "files_reviewed": artifact.files_reviewed,
        "reviewer": artifact.reviewer,
        "downstream_consumer": artifact.downstream_consumer,
        "bundle_summary": artifact.bundle_summary,
        "metadata": artifact.metadata,
        "provenance": artifact.provenance,
        "matches": artifact.matches,
    }


def _summarize_missing_behavior(insufficiency_reasons: list[str]) -> str:
    if not insufficiency_reasons:
        return ""
    return "missing behavior: " + ", ".join(insufficiency_reasons)


def _normalized_bundle_summary(artifact: EvaluationArtifact) -> dict[str, Any]:
    return {
        "bundle_dir": str(artifact.bundle_summary.get("bundle_dir", "")),
        "bundle_kind": str(artifact.bundle_summary.get("bundle_kind", "")),
        "contract_versions": dict(artifact.bundle_summary.get("contract_versions", {})),
        "primary_record_path": str(artifact.bundle_summary.get("primary_record_path", "")),
        "primary_record_present": bool(artifact.bundle_summary.get("primary_record_present", False)),
        "import_ready": bool(artifact.bundle_summary.get("import_ready", False)),
        "import_validation_status": str(artifact.bundle_summary.get("import_validation_status", "")),
        "graph_stats": dict(artifact.bundle_summary.get("graph_stats", {})),
    }


def _render_contract_version_lines(contract_versions: dict[str, Any]) -> list[str]:
    if not contract_versions:
        return ["- (none)"]
    return [
        f"- `{name}`: `{value}`"
        for name, value in sorted(contract_versions.items())
    ]


def _render_source_count_summary(source_match_counts: dict[str, Any]) -> str:
    if not source_match_counts:
        return "(none)"
    return ", ".join(f"{source}={count}" for source, count in source_match_counts.items())


def _render_reason_summary(reasons: list[Any]) -> str:
    if not reasons:
        return "(none)"
    return ", ".join(str(reason) for reason in reasons)


def _render_record_id_summary(record_ids: list[Any]) -> str:
    if not record_ids:
        return "(none)"
    return ", ".join(f"`{record_id}`" for record_id in record_ids)


def _require_artifact_keys(payload: dict[str, Any], required_keys: set[str]) -> None:
    missing_keys = sorted(key for key in required_keys if key not in payload)
    if missing_keys:
        joined = ", ".join(missing_keys)
        raise EvaluationArtifactValidationError(
            f"evaluation artifact is missing required keys: {joined}"
        )


def _require_dict_field(value: Any, *, field_name: str) -> None:
    if not isinstance(value, dict):
        raise EvaluationArtifactValidationError(
            f"evaluation artifact field {field_name} must decode to an object"
        )


def _require_list_field(value: Any, *, field_name: str) -> None:
    if not isinstance(value, list):
        raise EvaluationArtifactValidationError(
            f"evaluation artifact field {field_name} must decode to a list"
        )


def _require_string_list_entries(values: list[Any], *, field_name: str) -> None:
    for index, value in enumerate(values):
        if not isinstance(value, str):
            raise EvaluationArtifactValidationError(
                f"evaluation artifact field {field_name} entry {index} must decode to a string"
            )


def _require_dict_list_entries(values: list[Any], *, field_name: str) -> None:
    for index, value in enumerate(values):
        if not isinstance(value, dict):
            raise EvaluationArtifactValidationError(
                f"evaluation artifact field {field_name} entry {index} must decode to an object"
            )


def _require_match_entry_keys(matches: list[Any]) -> None:
    required_keys = {"identifier", "source_record_id", "source"}
    for index, match in enumerate(matches):
        missing_keys = sorted(key for key in required_keys if key not in match)
        if missing_keys:
            joined = ", ".join(missing_keys)
            raise EvaluationArtifactValidationError(
                f"evaluation artifact field matches entry {index} is missing required keys: {joined}"
            )
