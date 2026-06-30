from __future__ import annotations

from typing import Any

from chronicle_external_query.retrieval.contracts import (
    RetrievalMatch,
    RetrievalProvenance,
    RetrievalResult,
    VectorRetrieverProtocol,
)
from chronicle_external_query.retrieval.graph_retriever import GraphRetriever
from chronicle_external_query.retrieval.vector_retriever import VectorRetriever


class HybridRetriever:
    def __init__(self, *, vector_retriever: VectorRetrieverProtocol | None = None) -> None:
        self.graph = GraphRetriever()
        self.vector = vector_retriever or VectorRetriever()

    def search(self, graph_payload: dict[str, Any], query: str, limit: int = 5) -> RetrievalResult:
        graph_result = self.graph.search(graph_payload, query=query, limit=limit)
        vector_matches = self.vector.search(query=query, limit=limit)
        matches, overlap_source_record_ids = self._merge_matches(
            graph_matches=graph_result.matches,
            vector_matches=vector_matches,
            limit=limit,
        )
        insufficiency_reasons = list(graph_result.provenance.insufficiency_reasons)
        if not vector_matches:
            insufficiency_reasons.append("vector_unavailable")
        if not matches and "no_matches" not in insufficiency_reasons:
            insufficiency_reasons.append("no_matches")
        provenance = RetrievalProvenance(
            query=query,
            retrieval_mode="hybrid",
            sources=("graph", "vector"),
            match_count=len(matches),
            graph_node_count=graph_result.provenance.graph_node_count,
            graph_edge_count=graph_result.provenance.graph_edge_count,
            source_match_counts={
                "graph": len(graph_result.matches),
                "vector": len(vector_matches),
                "merged": len(matches),
            },
            overlap_source_record_ids=overlap_source_record_ids,
            insufficiency_reasons=tuple(dict.fromkeys(insufficiency_reasons)),
        )
        return RetrievalResult(
            query=query,
            retrieval_mode="hybrid",
            matches=matches,
            provenance=provenance,
        )

    def _merge_matches(
        self,
        *,
        graph_matches: list[RetrievalMatch],
        vector_matches: list[RetrievalMatch],
        limit: int,
    ) -> tuple[list[RetrievalMatch], tuple[str, ...]]:
        merged: dict[str, RetrievalMatch] = {}
        overlap_source_record_ids: list[str] = []

        for match in graph_matches:
            merged[match.source_record_id] = match

        for vector_match in vector_matches:
            existing = merged.get(vector_match.source_record_id)
            if existing is None:
                merged[vector_match.source_record_id] = vector_match
                continue

            overlap_source_record_ids.append(vector_match.source_record_id)
            merged[vector_match.source_record_id] = RetrievalMatch(
                source="hybrid_overlap",
                identifier=existing.identifier,
                source_record_id=existing.source_record_id,
                entity_type=existing.entity_type,
                title=existing.title or vector_match.title,
                summary=existing.summary or vector_match.summary,
                score=max(existing.score, vector_match.score),
                matched_terms=tuple(dict.fromkeys(existing.matched_terms + vector_match.matched_terms)),
                metadata={
                    "graph_metadata": existing.metadata,
                    "vector_metadata": vector_match.metadata,
                    "overlap_sources": ("graph", "vector"),
                    "graph_score": existing.score,
                    "vector_score": vector_match.score,
                },
            )

        ordered_matches = sorted(
            merged.values(),
            key=lambda item: (-item.score, item.identifier, item.source_record_id),
        )
        return ordered_matches[:limit], tuple(sorted(set(overlap_source_record_ids)))
