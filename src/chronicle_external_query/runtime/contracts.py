from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from chronicle_external_query.retrieval.contracts import RetrievalMatch, RetrievalProvenance


@dataclass(frozen=True)
class GeneratedAnswer:
    status: str
    answer_text: str
    metadata: dict[str, Any] = field(default_factory=dict)


class AnswerGeneratorProtocol(Protocol):
    generator_name: str

    def generate(
        self,
        *,
        query: str,
        matches: list[RetrievalMatch],
        provenance: RetrievalProvenance,
        prompt: str,
    ) -> GeneratedAnswer:
        ...


class AnswerGenerationError(ValueError):
    """Raised when an opt-in answer generator fails explicitly."""
