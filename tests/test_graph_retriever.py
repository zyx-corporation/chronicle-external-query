from __future__ import annotations

from chronicle_external_query.retrieval.graph_retriever import GraphRetriever


def test_graph_retriever_scores_matching_nodes():
    graph_payload = {
        "nodes": [
            {"node_id": "n_evt_2", "source_id": "evt_2", "node_type": "event", "title": "Graph query result"},
            {"node_id": "n_evt_1", "source_id": "evt_1", "node_type": "event", "title": "Chronicle bundle graph"},
            {"node_id": "n_evt_3", "source_id": "evt_3", "node_type": "event", "title": "Unrelated"},
        ],
        "edges": [],
    }

    result = GraphRetriever().search(graph_payload, query="graph chronicle", limit=5)

    assert result.retrieval_mode == "graph-only"
    assert [match.source_record_id for match in result.matches] == ["evt_1", "evt_2"]
    assert result.matches[0].score >= result.matches[1].score
    assert result.provenance.match_count == 2
    assert result.matches[0].metadata["matched_fields"]["title"] == ["graph", "chronicle"]


def test_graph_retriever_prefers_title_over_source_id_only_match():
    graph_payload = {
        "nodes": [
            {"node_id": "n_evt_1", "source_id": "graph-source", "node_type": "event", "title": "Unrelated"},
            {"node_id": "n_evt_2", "source_id": "evt_2", "node_type": "event", "title": "Graph focused title"},
        ],
        "edges": [],
    }

    result = GraphRetriever().search(graph_payload, query="graph", limit=5)

    assert [match.source_record_id for match in result.matches] == ["evt_2", "graph-source"]
    assert result.matches[0].metadata["matched_fields"] == {"title": ["graph"]}


def test_graph_retriever_deduplicates_source_record_ids_and_exposes_evidence_summary():
    graph_payload = {
        "nodes": [
            {
                "node_id": "n_event_evt_1",
                "source_id": "evt_1",
                "node_type": "event",
                "title": "Release Planning context added",
                "summary": "context event",
            },
            {
                "node_id": "n_source_evt_1",
                "source_id": "evt_1",
                "node_type": "event",
                "title": "evt_1",
                "summary": "",
            },
        ],
        "edges": [],
    }

    result = GraphRetriever().search(graph_payload, query="release planning context", limit=5)

    assert [match.source_record_id for match in result.matches] == ["evt_1"]
    assert result.matches[0].metadata["matched_field_count"] >= 1
    assert "title:release, planning, context" in result.matches[0].metadata["evidence_summary"]


def test_graph_retriever_reports_no_match_insufficiency():
    graph_payload = {
        "nodes": [
            {"node_id": "n_evt_1", "source_id": "evt_1", "node_type": "event", "title": "Chronicle bundle graph"},
        ],
        "edges": [],
    }

    result = GraphRetriever().search(graph_payload, query="vector only", limit=5)

    assert result.matches == []
    assert "no_graph_matches" in result.provenance.insufficiency_reasons
