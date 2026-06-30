from __future__ import annotations

from typing import Any

from chronicle_external_query.retrieval.contracts import (
    RetrievalMatch,
    RetrievalProvenance,
    RetrievalResult,
)


class GraphRetriever:
    """Simple label/text-based retrieval over Chronicle graph exports."""

    FIELD_WEIGHTS = {
        "title": 3.0,
        "summary": 2.0,
        "node_type": 1.5,
        "source_id": 1.0,
        "node_id": 0.5,
    }

    def search(self, graph_payload: dict[str, Any], query: str, limit: int = 5) -> RetrievalResult:
        lowered_terms = [term for term in query.lower().split() if term]
        if not lowered_terms:
            return self._result(
                graph_payload=graph_payload,
                query=query,
                matches=[],
                insufficiency_reasons=["empty_query"],
            )

        matches: list[RetrievalMatch] = []
        for node in graph_payload.get("nodes", []):
            if not isinstance(node, dict):
                continue
            score, matched_terms, matched_fields = self._score_node(node=node, query_terms=lowered_terms)
            if score:
                matches.append(
                    RetrievalMatch(
                        source="graph",
                        identifier=str(node.get("node_id", node.get("id", ""))),
                        source_record_id=str(node.get("source_id", node.get("id", ""))),
                        entity_type=str(node.get("node_type", node.get("type", ""))),
                        title=str(node.get("title", node.get("label", ""))),
                        summary=str(node.get("summary", "")),
                        score=score,
                        matched_terms=matched_terms,
                        metadata={
                            "graph_node_metadata": dict(node.get("metadata", {})),
                            "matched_fields": matched_fields,
                        },
                    )
                )
        matches.sort(key=lambda item: (-item.score, item.identifier, item.source_record_id))
        limited_matches = matches[:limit]
        insufficiency_reasons = [] if limited_matches else ["no_graph_matches"]
        return self._result(
            graph_payload=graph_payload,
            query=query,
            matches=limited_matches,
            insufficiency_reasons=insufficiency_reasons,
        )

    def _result(
        self,
        *,
        graph_payload: dict[str, Any],
        query: str,
        matches: list[RetrievalMatch],
        insufficiency_reasons: list[str],
    ) -> RetrievalResult:
        provenance = RetrievalProvenance(
            query=query,
            retrieval_mode="graph-only",
            sources=("graph",),
            match_count=len(matches),
            graph_node_count=len(graph_payload.get("nodes", [])),
            graph_edge_count=len(graph_payload.get("edges", [])),
            source_match_counts={"graph": len(matches)},
            insufficiency_reasons=tuple(insufficiency_reasons),
        )
        return RetrievalResult(
            query=query,
            retrieval_mode="graph-only",
            matches=matches,
            provenance=provenance,
        )

    def _score_node(
        self,
        *,
        node: dict[str, Any],
        query_terms: list[str],
    ) -> tuple[float, tuple[str, ...], dict[str, list[str]]]:
        matched_terms: list[str] = []
        matched_fields: dict[str, list[str]] = {}
        score = 0.0

        for field, weight in self.FIELD_WEIGHTS.items():
            field_value = str(node.get(field, node.get(field.replace("node_", ""), ""))).lower()
            if not field_value:
                continue
            field_matches = [term for term in query_terms if term in field_value]
            if not field_matches:
                continue
            score += weight * len(field_matches)
            matched_fields[field] = field_matches
            matched_terms.extend(field_matches)

        unique_terms = tuple(dict.fromkeys(matched_terms))
        return score, unique_terms, matched_fields
