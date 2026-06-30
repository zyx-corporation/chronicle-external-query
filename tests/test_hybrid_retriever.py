from __future__ import annotations

from pathlib import Path

import pytest

from chronicle_external_query.models import VectorFixtureValidationError
from chronicle_external_query.retrieval.contracts import RetrievalMatch
from chronicle_external_query.retrieval.hybrid_retriever import HybridRetriever
from chronicle_external_query.retrieval.vector_adapter import StaticVectorRetriever, load_static_vector_retriever


def test_hybrid_retriever_returns_shared_result_shape():
    graph_payload = {
        "nodes": [
            {"node_id": "n_evt_1", "source_id": "evt_1", "node_type": "event", "title": "Chronicle graph bundle"},
        ],
        "edges": [],
    }

    result = HybridRetriever().search(graph_payload, query="chronicle graph", limit=5)

    assert result.retrieval_mode == "hybrid"
    assert result.provenance.sources == ("graph", "vector")
    assert result.matches[0].source == "graph"
    assert "vector_unavailable" in result.provenance.insufficiency_reasons


def test_hybrid_retriever_marks_overlap_and_source_counts():
    graph_payload = {
        "nodes": [
            {"node_id": "n_evt_1", "source_id": "evt_1", "node_type": "event", "title": "Chronicle graph bundle"},
            {"node_id": "n_evt_2", "source_id": "evt_2", "node_type": "event", "title": "Second graph node"},
        ],
        "edges": [],
    }
    vector_retriever = StaticVectorRetriever(
        matches=(
            RetrievalMatch(
                source="vector",
                identifier="v_evt_1",
                source_record_id="evt_1",
                entity_type="event",
                title="Chronicle graph bundle",
                summary="vector overlap",
                score=3.0,
                matched_terms=("chronicle",),
                metadata={"provider": "static"},
            ),
            RetrievalMatch(
                source="vector",
                identifier="v_evt_3",
                source_record_id="evt_3",
                entity_type="event",
                title="Vector-only node",
                summary="vector only",
                score=2.0,
                matched_terms=("vector",),
                metadata={"provider": "static"},
            ),
        )
    )

    result = HybridRetriever(vector_retriever=vector_retriever).search(
        graph_payload,
        query="chronicle vector",
        limit=5,
    )

    assert result.provenance.source_match_counts == {"graph": 1, "vector": 2, "merged": 2}
    assert result.provenance.overlap_source_record_ids == ("evt_1",)
    assert [match.source_record_id for match in result.matches] == ["evt_1", "evt_3"]
    assert result.matches[0].source == "hybrid_overlap"
    assert result.matches[0].metadata["graph_score"] >= result.matches[0].metadata["vector_score"]
    assert result.matches[0].metadata["overlap_sources"] == ("graph", "vector")


def test_hybrid_retriever_preserves_vector_only_results():
    graph_payload = {"nodes": [], "edges": []}
    vector_retriever = StaticVectorRetriever(
        matches=(
            RetrievalMatch(
                source="vector",
                identifier="v_evt_9",
                source_record_id="evt_9",
                entity_type="event",
                title="Vector-only node",
                summary="vector fallback",
                score=1.0,
                matched_terms=("vector",),
                metadata={"provider": "static"},
            ),
        )
    )

    result = HybridRetriever(vector_retriever=vector_retriever).search(
        graph_payload,
        query="vector",
        limit=5,
    )

    assert [match.source_record_id for match in result.matches] == ["evt_9"]
    assert result.provenance.source_match_counts == {"graph": 0, "vector": 1, "merged": 1}
    assert "vector_unavailable" not in result.provenance.insufficiency_reasons


def test_load_static_vector_retriever_from_fixture():
    fixture_path = (
        Path(__file__).resolve().parent
        / "fixtures"
        / "vector_matches"
        / "sample-vector-matches.json"
    )

    retriever = load_static_vector_retriever(fixture_path)
    matches = retriever.search(query="fixture vector", limit=5)

    assert [match.source_record_id for match in matches] == [
        "evt_68ab2b1818b64b0daae09a02228e6d38",
        "evt_vector_only",
    ]


def test_load_static_vector_retriever_rejects_invalid_root_shape(tmp_path: Path):
    fixture_path = tmp_path / "invalid-root.json"
    fixture_path.write_text('{"identifier": "v_evt_1"}', encoding="utf-8")

    with pytest.raises(VectorFixtureValidationError, match="must decode to a list"):
        load_static_vector_retriever(fixture_path)


def test_load_static_vector_retriever_rejects_missing_required_keys(tmp_path: Path):
    fixture_path = tmp_path / "missing-keys.json"
    fixture_path.write_text('[{"identifier": "v_evt_1"}]', encoding="utf-8")

    with pytest.raises(
        VectorFixtureValidationError,
        match="must include identifier and source_record_id",
    ):
        load_static_vector_retriever(fixture_path)
