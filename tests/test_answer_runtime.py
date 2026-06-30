from __future__ import annotations

import json

from chronicle_external_query.evaluation.result_serializer import serialize_runtime_answer
from chronicle_external_query.runtime.answer_runtime import AnswerRuntime


def test_answer_runtime_returns_prompt_and_metadata():
    graph_payload = {
        "nodes": [
            {"node_id": "n_evt_1", "source_id": "evt_1", "node_type": "event", "title": "Chronicle graph bundle"},
        ],
        "edges": [],
    }

    answer = AnswerRuntime().answer(graph_payload, query="chronicle graph")

    assert answer.status == "answered"
    assert "Top grounded record" in answer.answer_text
    assert answer.metadata["retrieval_mode"] == "graph-only"
    assert answer.metadata["match_count"] == 1
    assert answer.metadata["sources"] == ["graph"]
    assert answer.metadata["top_match_source_record_ids"] == ["evt_1"]
    assert answer.metadata["top_match_sources"] == ["graph"]
    assert answer.metadata["coverage_summary"]["match_count"] == 1
    assert "Query: chronicle graph" in answer.prompt
    assert answer.graph_matches[0].source_record_id == "evt_1"


def test_answer_runtime_reports_insufficient_context_when_no_matches():
    graph_payload = {"nodes": [], "edges": []}

    answer = AnswerRuntime().answer(graph_payload, query="chronicle graph")

    assert answer.status == "insufficient_context"
    assert "No sufficiently grounded matches" in answer.answer_text
    assert "no_graph_matches" in answer.metadata["insufficiency_reasons"]


def test_serialized_runtime_answer_exposes_chronicle_alignment_fields():
    graph_payload = {
        "nodes": [
            {"node_id": "n_evt_1", "source_id": "evt_1", "node_type": "event", "title": "Chronicle graph bundle"},
        ],
        "edges": [],
    }

    payload = json.loads(serialize_runtime_answer(AnswerRuntime().answer(graph_payload, query="chronicle graph")))

    assert payload["sufficient"] is True
    assert payload["chronicle_trial_alignment"]["record_kind"] == "query_engine_bundle_trial"
    assert payload["chronicle_trial_alignment"]["sufficient"] is True
