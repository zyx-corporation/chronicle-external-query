from __future__ import annotations

import pytest

from chronicle_external_query.plugins import load_provider_plugin
from chronicle_external_query.plugins.gemma4.answer_generator import Gemma4AnswerGenerator
from chronicle_external_query.retrieval.contracts import RetrievalMatch, RetrievalProvenance


pytestmark = [pytest.mark.provider_plugin, pytest.mark.gemma4]


def test_gemma4_plugin_becomes_available_with_local_config(monkeypatch):
    monkeypatch.setenv("GEMMA4_ENABLED", "true")
    monkeypatch.setenv("GEMMA4_BASE_URL", "http://127.0.0.1:11434")
    monkeypatch.setenv("GEMMA4_MODEL", "gemma4")

    plugin = load_provider_plugin("gemma4")
    status = plugin.describe_status()

    assert plugin.is_available() is True
    assert status.available is True
    assert status.availability_reason == "configured"
    assert status.metadata["supports_answer_generation"] is True


def test_gemma4_answer_generator_calls_local_runtime(monkeypatch):
    monkeypatch.setenv("GEMMA4_ENABLED", "true")
    monkeypatch.setenv("GEMMA4_BASE_URL", "http://127.0.0.1:11434")
    monkeypatch.setenv("GEMMA4_MODEL", "gemma4")

    captured: dict[str, object] = {}

    def fake_post(config, body):
        captured["base_url"] = config.base_url
        captured["model"] = config.model
        captured["body"] = body
        return {
            "choices": [
                {
                    "message": {
                        "content": "grounded gemma4 answer",
                    }
                }
            ]
        }

    monkeypatch.setattr(
        "chronicle_external_query.plugins.gemma4.answer_generator._post_chat_completion",
        fake_post,
    )

    plugin = load_provider_plugin("gemma4")
    generator = plugin.build_answer_generator()
    result = generator.generate(
        query="release planning context",
        matches=[
            RetrievalMatch(
                identifier="m_evt_1",
                source_record_id="evt_1",
                entity_type="event",
                title="Release Planning",
                summary="Planning summary",
                score=3.0,
                source="graph",
                matched_terms=("release", "planning"),
                metadata={},
            )
        ],
        provenance=RetrievalProvenance(
            query="release planning context",
            retrieval_mode="graph-only",
            sources=("graph",),
            match_count=1,
            graph_node_count=1,
            graph_edge_count=0,
            source_match_counts={"graph": 1},
            overlap_source_record_ids=(),
            insufficiency_reasons=(),
        ),
        prompt="Query: release planning context",
    )

    assert isinstance(generator, Gemma4AnswerGenerator)
    assert result.answer_text == "grounded gemma4 answer"
    assert result.metadata["answer_generator"] == "gemma4"
    assert captured["base_url"] == "http://127.0.0.1:11434"
    assert captured["model"] == "gemma4"
    assert captured["body"]["messages"][1]["content"] == "Query: release planning context"
