from __future__ import annotations

import json
from typing import Any

from chronicle_external_query.evaluation.artifacts import (
    build_chronicle_trial_alignment,
    build_evaluation_artifact,
)
from chronicle_external_query.runtime.answer_runtime import RuntimeAnswer


def serialize_runtime_answer(answer: RuntimeAnswer) -> str:
    artifact = build_evaluation_artifact(answer)
    payload: dict[str, Any] = {
        "artifact_version": artifact.artifact_version,
        "query": artifact.query,
        "runtime_status": artifact.runtime_status,
        "retrieval_mode": artifact.retrieval_mode,
        "answer_text": artifact.answer_text,
        "prompt": answer.prompt,
        "sufficient": artifact.sufficient,
        "missing_behavior": artifact.missing_behavior,
        "files_reviewed": artifact.files_reviewed,
        "reviewer": artifact.reviewer,
        "downstream_consumer": artifact.downstream_consumer,
        "metadata": artifact.metadata,
        "provenance": artifact.provenance,
        "graph_matches": artifact.matches,
        "chronicle_trial_alignment": build_chronicle_trial_alignment(artifact),
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)
