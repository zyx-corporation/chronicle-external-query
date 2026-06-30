from __future__ import annotations

from chronicle_external_query.retrieval.contracts import RetrievalMatch


def build_answer_prompt(query: str, matches: list[RetrievalMatch]) -> str:
    context_lines = [f"- {match.identifier}: {match.title}" for match in matches]
    context_block = "\n".join(context_lines) if context_lines else "- no graph matches"
    return f"Query: {query}\nContext:\n{context_block}"
