from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib import request
from urllib.error import HTTPError, URLError

from chronicle_external_query.retrieval.contracts import RetrievalMatch, RetrievalProvenance
from chronicle_external_query.runtime.contracts import AnswerGenerationError, AnswerGeneratorProtocol, GeneratedAnswer

from .config import Gemma4Config


@dataclass(frozen=True)
class Gemma4AnswerGenerator(AnswerGeneratorProtocol):
    config: Gemma4Config
    generator_name: str = "gemma4"

    def generate(
        self,
        *,
        query: str,
        matches: list[RetrievalMatch],
        provenance: RetrievalProvenance,
        prompt: str,
    ) -> GeneratedAnswer:
        body = {
            "model": self.config.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a local downstream reviewer. Ground every answer in the provided "
                        "Chronicle-derived context and do not invent unsupported facts."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.0,
            "stream": False,
        }
        payload = _post_chat_completion(self.config, body)
        answer_text = _extract_answer_text(payload)
        return GeneratedAnswer(
            status="answered" if matches else "insufficient_context",
            answer_text=answer_text,
            metadata={
                "answer_generator": self.generator_name,
                "answer_generator_mode": "local_plugin",
                "answer_generator_fallback_used": False,
                "answer_generator_model": self.config.model,
                "answer_generator_base_url": self.config.base_url,
                "answer_generator_match_count": len(matches),
                "answer_generator_provenance_sources": list(provenance.sources),
            },
        )


def _post_chat_completion(config: Gemma4Config, body: dict[str, Any]) -> dict[str, Any]:
    endpoint = f"{config.base_url}/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
    }
    if config.api_key:
        headers["Authorization"] = f"Bearer {config.api_key}"

    req = request.Request(
        endpoint,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=config.timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise AnswerGenerationError(
            f"gemma4 plugin request failed with HTTP {exc.code}: {endpoint}"
        ) from exc
    except URLError as exc:
        raise AnswerGenerationError(
            f"gemma4 plugin could not reach local runtime: {endpoint}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise AnswerGenerationError(
            f"gemma4 plugin returned invalid JSON: {endpoint}"
        ) from exc

    if not isinstance(payload, dict):
        raise AnswerGenerationError("gemma4 plugin response must decode to an object")
    return payload


def _extract_answer_text(payload: dict[str, Any]) -> str:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise AnswerGenerationError("gemma4 plugin response must include a non-empty choices list")
    first_choice = choices[0]
    if not isinstance(first_choice, dict):
        raise AnswerGenerationError("gemma4 plugin choice entry must decode to an object")
    message = first_choice.get("message")
    if not isinstance(message, dict):
        raise AnswerGenerationError("gemma4 plugin response must include a message object")
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise AnswerGenerationError("gemma4 plugin response must include non-empty message content")
    return content.strip()
