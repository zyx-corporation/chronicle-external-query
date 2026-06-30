from __future__ import annotations

from chronicle_external_query.retrieval.contracts import RetrievalMatch
from chronicle_external_query.retrieval.vector_adapter import NullVectorRetriever


class VectorRetriever(NullVectorRetriever):
    """Compatibility alias for the default provider-neutral null adapter."""

    def search(self, query: str, limit: int = 5) -> list[RetrievalMatch]:
        return super().search(query=query, limit=limit)
