from __future__ import annotations

from chronicle_external_query.retrieval.contracts import RetrievalMatch


def rank_graph_matches(matches: list[RetrievalMatch]) -> list[RetrievalMatch]:
    return sorted(matches, key=lambda item: (-item.score, item.identifier, item.source_record_id))
