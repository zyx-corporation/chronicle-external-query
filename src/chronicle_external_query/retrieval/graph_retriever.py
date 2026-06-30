from __future__ import annotations

import re
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
    TOKEN_MATCH_FIELDS = {"node_type", "source_id", "node_id"}

    def search(self, graph_payload: dict[str, Any], query: str, limit: int = 5) -> RetrievalResult:
        lowered_terms = [term for term in query.lower().split() if term]
        if not lowered_terms:
            return self._result(
                graph_payload=graph_payload,
                query=query,
                matches=[],
                insufficiency_reasons=["empty_query"],
            )

        best_by_source_record_id: dict[str, RetrievalMatch] = {}
        for node in graph_payload.get("nodes", []):
            if not isinstance(node, dict):
                continue
            score, matched_terms, matched_fields = self._score_node(node=node, query_terms=lowered_terms)
            if score:
                match = RetrievalMatch(
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
                        "matched_field_count": len(matched_fields),
                        "evidence_summary": self._build_evidence_summary(matched_fields),
                    },
                )
                existing = best_by_source_record_id.get(match.source_record_id)
                if existing is None or self._is_better_match(match, existing):
                    best_by_source_record_id[match.source_record_id] = match
        matches = list(best_by_source_record_id.values())
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
            raw_value = str(node.get(field, node.get(field.replace("node_", ""), "")))
            field_value = raw_value.lower()
            if not field_value.strip():
                continue
            field_matches = self._match_terms(field=field, field_value=field_value, query_terms=query_terms)
            if not field_matches:
                continue
            score += weight * len(field_matches)
            matched_fields[field] = field_matches
            matched_terms.extend(field_matches)

        unique_terms = tuple(dict.fromkeys(matched_terms))
        return score, unique_terms, matched_fields

    def _match_terms(self, *, field: str, field_value: str, query_terms: list[str]) -> list[str]:
        if field in self.TOKEN_MATCH_FIELDS:
            tokens = set(self._tokenize(field_value))
            return [term for term in query_terms if term in tokens]
        return [term for term in query_terms if term in field_value]

    def _tokenize(self, value: str) -> list[str]:
        return [token for token in re.split(r"[^a-z0-9]+", value.lower()) if token]

    def _build_evidence_summary(self, matched_fields: dict[str, list[str]]) -> list[str]:
        return [
            f"{field}:{', '.join(terms)}"
            for field, terms in matched_fields.items()
        ]

    def _is_better_match(self, candidate: RetrievalMatch, current: RetrievalMatch) -> bool:
        if candidate.score != current.score:
            return candidate.score > current.score
        if candidate.identifier != current.identifier:
            return candidate.identifier < current.identifier
        return candidate.source_record_id < current.source_record_id
