from __future__ import annotations

import json
from pathlib import Path

from chronicle_external_query.retrieval.graph_retriever import GraphRetriever


FIXTURE_GRAPH_JSON = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "query_engine_bundle"
    / "minimal_cli_bundle"
    / "graph.json"
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
