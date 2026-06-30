from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from chronicle_external_query.retrieval.contracts import (
    RetrievalMatch,
    RetrievalProvenance,
    RetrievalResult,
    VectorRetrieverProtocol,
)
from chronicle_external_query.retrieval.graph_retriever import GraphRetriever
from chronicle_external_query.retrieval.hybrid_retriever import HybridRetriever
from chronicle_external_query.runtime.contracts import AnswerGeneratorProtocol
from chronicle_external_query.runtime.prompts import build_answer_prompt
from chronicle_external_query.runtime.ranking import rank_graph_matches


@dataclass(frozen=True)
class RuntimeAnswer:
    query: str
    status: str
    answer_text: str
    prompt: str
    graph_matches: list[RetrievalMatch]
    provenance: RetrievalProvenance
    metadata: dict[str, Any]


class AnswerRuntime:
    def __init__(
        self,
        *,
        mode: str = "graph",
        vector_retriever: VectorRetrieverProtocol | None = None,
        answer_generator: AnswerGeneratorProtocol | None = None,
    ) -> None:
        self.mode = mode
        self.graph = GraphRetriever()
        self.hybrid = HybridRetriever(vector_retriever=vector_retriever)
        self.answer_generator = answer_generator

    def answer(self, graph_payload: dict[str, Any], query: str, limit: int = 5) -> RuntimeAnswer:
        retrieval = self._retrieve(graph_payload=graph_payload, query=query, limit=limit)
        ranked = rank_graph_matches(retrieval.matches)
        prompt = build_answer_prompt(query=query, matches=ranked)
        status = "answered" if ranked else "insufficient_context"
        answer_text = self._build_answer_text(query=query, matches=ranked)
        generator_metadata: dict[str, Any] = {
            "answer_generator": "deterministic_baseline",
            "answer_generator_mode": "builtin",
            "answer_generator_fallback_used": False,
        }
        if ranked and self.answer_generator is not None:
            generated = self.answer_generator.generate(
                query=query,
                matches=ranked,
                provenance=retrieval.provenance,
                prompt=prompt,
            )
            status = generated.status
            answer_text = generated.answer_text
            generator_metadata = dict(generated.metadata)
        metadata = {
            "status": status,
            "retrieval_mode": retrieval.retrieval_mode,
            "match_count": len(ranked),
            "sources": list(retrieval.provenance.sources),
            "source_match_counts": retrieval.provenance.source_match_counts,
            "overlap_source_record_ids": list(retrieval.provenance.overlap_source_record_ids),
            "insufficiency_reasons": list(retrieval.provenance.insufficiency_reasons),
            "top_match_source_record_ids": [match.source_record_id for match in ranked[:3]],
            "top_match_sources": [match.source for match in ranked[:3]],
            "coverage_summary": self._coverage_summary(retrieval.provenance),
            **generator_metadata,
        }
        return RuntimeAnswer(
            query=query,
            status=status,
            answer_text=answer_text,
            prompt=prompt,
            graph_matches=ranked,
            provenance=retrieval.provenance,
            metadata=metadata,
        )

    def _retrieve(self, *, graph_payload: dict[str, Any], query: str, limit: int) -> RetrievalResult:
        if self.mode == "hybrid":
            return self.hybrid.search(graph_payload, query=query, limit=limit)
        return self.graph.search(graph_payload, query=query, limit=limit)

    def _build_answer_text(self, *, query: str, matches: list[RetrievalMatch]) -> str:
        if not matches:
            return (
                f"No sufficiently grounded matches were found for '{query}'. "
                "Downstream runtime review should remain explicit about missing context."
            )
        if len(matches) == 1:
            match = matches[0]
            return (
                f"Top grounded record for '{query}': {match.title} "
                f"({match.source_record_id}, score={match.score:.1f})."
            )
        top = matches[0]
        return (
            f"Top grounded record for '{query}': {top.title} "
            f"({top.source_record_id}, score={top.score:.1f}); "
            f"{len(matches) - 1} additional supporting matches available."
        )

    def _coverage_summary(self, provenance: RetrievalProvenance) -> dict[str, Any]:
        return {
            "match_count": provenance.match_count,
            "graph_node_count": provenance.graph_node_count,
            "graph_edge_count": provenance.graph_edge_count,
            "insufficiency_reasons": list(provenance.insufficiency_reasons),
        }
