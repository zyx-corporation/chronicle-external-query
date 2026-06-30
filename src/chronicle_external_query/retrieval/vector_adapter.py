from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from chronicle_external_query.models import VectorFixtureValidationError
from chronicle_external_query.retrieval.contracts import RetrievalMatch, VectorRetrieverProtocol


@dataclass(frozen=True)
class StaticVectorRetriever(VectorRetrieverProtocol):
    """Deterministic provider-neutral retriever for tests and local fallback."""

    matches: tuple[RetrievalMatch, ...] = ()

    def search(self, query: str, limit: int = 5) -> list[RetrievalMatch]:
        return list(self.matches[:limit])


class NullVectorRetriever(VectorRetrieverProtocol):
    """Default provider-neutral fallback that returns no vector results."""

    def search(self, query: str, limit: int = 5) -> list[RetrievalMatch]:
        return []


def load_static_vector_retriever(path: Path) -> StaticVectorRetriever:
    if not path.exists():
        raise VectorFixtureValidationError(f"vector fixture file was not found: {path}")

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise VectorFixtureValidationError(
            f"vector fixture contains invalid JSON: {path}"
        ) from exc
    if not isinstance(payload, list):
        raise VectorFixtureValidationError("vector fixture must decode to a list")

    matches: list[RetrievalMatch] = []
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise VectorFixtureValidationError(
                f"vector fixture entry {index} must decode to an object"
            )
        if "identifier" not in item or "source_record_id" not in item:
            raise VectorFixtureValidationError(
                f"vector fixture entry {index} must include identifier and source_record_id"
            )
        matched_terms = item.get("matched_terms", [])
        if not isinstance(matched_terms, list):
            raise VectorFixtureValidationError(
                f"vector fixture entry {index} matched_terms must decode to a list"
            )
        metadata = item.get("metadata", {})
        if not isinstance(metadata, dict):
            raise VectorFixtureValidationError(
                f"vector fixture entry {index} metadata must decode to an object"
            )
        matches.append(
            RetrievalMatch(
                source=str(item.get("source", "vector")),
                identifier=str(item["identifier"]),
                source_record_id=str(item["source_record_id"]),
                entity_type=str(item.get("entity_type", "")),
                title=str(item.get("title", "")),
                summary=str(item.get("summary", "")),
                score=float(item.get("score", 0.0)),
                matched_terms=tuple(str(term) for term in matched_terms),
                metadata=dict(metadata),
            )
        )
    return StaticVectorRetriever(matches=tuple(matches))
