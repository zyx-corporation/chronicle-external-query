from __future__ import annotations

import json
from pathlib import Path

from chronicle_external_query.retrieval.graph_retriever import GraphRetriever
from chronicle_external_query.retrieval.hybrid_retriever import HybridRetriever
from chronicle_external_query.retrieval.vector_adapter import load_static_vector_retriever


FIXTURE_GRAPH_JSON = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "query_engine_bundle"
    / "minimal_cli_bundle"
    / "graph.json"
)
REPRESENTATIVE_FIXTURE_BUNDLE_DIR = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "query_engine_bundle"
    / "representative_cli_bundle"
)
REPRESENTATIVE_VECTOR_FIXTURE = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "vector_matches"
    / "representative-vector-matches.json"
)


def test_graph_retriever_handles_real_bundle_graph_fixture():
    graph_payload = json.loads(FIXTURE_GRAPH_JSON.read_text(encoding="utf-8"))

    result = GraphRetriever().search(graph_payload, query="fixture bundle", limit=5)

    assert result.retrieval_mode == "graph-only"
    assert result.provenance.graph_node_count == 2
    assert [match.source_record_id for match in result.matches] == [
        "chr_d6cb25478ffa4f48844d12a21c32e3b8",
        "evt_68ab2b1818b64b0daae09a02228e6d38",
    ]
    assert result.provenance.source_match_counts == {"graph": 2}


def test_graph_retriever_handles_representative_bundle_graph_fixture():
    graph_payload = json.loads((REPRESENTATIVE_FIXTURE_BUNDLE_DIR / "graph.json").read_text(encoding="utf-8"))

    result = GraphRetriever().search(graph_payload, query="release planning follow-up context", limit=5)

    assert result.retrieval_mode == "graph-only"
    assert result.provenance.graph_node_count == 8
    assert result.provenance.source_match_counts == {"graph": 4}
    assert [match.source_record_id for match in result.matches] == [
        "evt_context_release_planning",
        "ctx_release_planning",
        "evt_context_incident_follow_up",
        "ctx_incident_follow_up",
    ]
    assert "title:release, planning, context" in result.matches[0].metadata["evidence_summary"]


def test_hybrid_retriever_handles_representative_bundle_with_overlap_and_vector_only_support():
    graph_payload = json.loads((REPRESENTATIVE_FIXTURE_BUNDLE_DIR / "graph.json").read_text(encoding="utf-8"))
    vector_retriever = load_static_vector_retriever(REPRESENTATIVE_VECTOR_FIXTURE)

    result = HybridRetriever(vector_retriever=vector_retriever).search(
        graph_payload,
        query="release planning follow-up context",
        limit=5,
    )

    assert result.retrieval_mode == "hybrid"
    assert result.provenance.source_match_counts == {"graph": 4, "vector": 2, "merged": 5}
    assert result.provenance.overlap_source_record_ids == ("ctx_release_planning",)
    assert [match.source_record_id for match in result.matches] == [
        "evt_context_release_planning",
        "ctx_release_planning",
        "evt_context_incident_follow_up",
        "ctx_incident_follow_up",
        "evt_follow_up_vector_only",
    ]
    overlap_match = result.matches[1]
    assert overlap_match.source == "hybrid_overlap"
    assert overlap_match.metadata["graph_score"] == 15.0
    assert overlap_match.metadata["vector_score"] == 4.0
