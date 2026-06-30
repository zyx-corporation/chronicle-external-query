from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol
from typing import Any


@dataclass(frozen=True)
class RetrievalMatch:
    source: str
    identifier: str
    source_record_id: str
    entity_type: str
    title: str
    summary: str
    score: float
    matched_terms: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RetrievalProvenance:
    query: str
    retrieval_mode: str
    sources: tuple[str, ...]
    match_count: int
    graph_node_count: int
    graph_edge_count: int
    source_match_counts: dict[str, int] = field(default_factory=dict)
    overlap_source_record_ids: tuple[str, ...] = ()
    insufficiency_reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class RetrievalResult:
    query: str
    retrieval_mode: str
    matches: list[RetrievalMatch]
    provenance: RetrievalProvenance


class VectorRetrieverProtocol(Protocol):
    def search(self, query: str, limit: int = 5) -> list[RetrievalMatch]:
        ...
