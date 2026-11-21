import logging
import time
from collections.abc import Sequence

import orjson
from openai import APITimeoutError, AsyncOpenAI

from src.application.answers.dtos import AnswerBlock, AnswerDraft, AnswerSource, AnswerStatus
from src.application.answers.exceptions import InvalidGeneratedAnswerError
from src.application.answers.models import AnswerUsage
from src.application.answers.types import GeneratedAnswer

from . import prompts
from .config import AiTunnelConfig

logger = logging.getLogger(__name__)


class AiTunnelAnswerGenerator:
    def __init__(self, config: AiTunnelConfig, *, max_output_tokens: int = 800) -> None:
        self._config = config
        self._max_output_tokens = max_output_tokens
        self._client = AsyncOpenAI(
            api_key=config.api_key.get_secret_value(),
            base_url=str(config.base_url),
            timeout=float(config.timeout),
            max_retries=config.max_retries,
        )

    @property
    def model_id(self) -> str:
        return self._config.answer_model

    @property
    def provider(self) -> str:
        return "aitunnel"

    async def generate(self, question: str, sources: Sequence[AnswerSource]) -> GeneratedAnswer:
        user_payload = {
            "question": question,
            "sources": [
                {
                    "id": source.id,
                    "title": source.title,
                    "excerpt": source.excerpt,
                }
                for source in sources
            ],
        }

        started = time.perf_counter()
        try:
            response = await self._client.chat.completions.create(
                model=self._config.answer_model,
                response_format={"type": "json_object"},
                temperature=0,
                max_tokens=self._max_output_tokens,
                messages=[
                    {"role": "system", "content": prompts.ANSWER_SYSTEM},
                    {
                        "role": "user",
                        "content": orjson.dumps(user_payload).decode(),
                    },
                ],
            )
        except APITimeoutError as exc:
            raise TimeoutError("LLM timeout") from exc

        generation_ms = int((time.perf_counter() - started) * 1000)
        usage = _extract_usage(response)
        raw = response.choices[0].message.content if response.choices else None
        if not raw:
            raise InvalidGeneratedAnswerError("Empty LLM content")

        draft = _parse_draft(raw)
        return GeneratedAnswer(
            draft=draft,
            usage=usage,
            provider=self.provider,
            model_id=self.model_id,
            generation_ms=generation_ms,
        )

    async def close(self) -> None:
        await self._client.close()


def _extract_usage(response: object) -> AnswerUsage | None:
    usage = getattr(response, "usage", None)
    if usage is None:
        return None

    input_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
    output_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
    details = getattr(usage, "prompt_tokens_details", None)
    cached = int(getattr(details, "cached_tokens", 0) or 0) if details is not None else 0
    completion_details = getattr(usage, "completion_tokens_details", None)
    reasoning = None
    if completion_details is not None:
        raw_reasoning = getattr(completion_details, "reasoning_tokens", None)
        reasoning = int(raw_reasoning) if raw_reasoning is not None else None

    return AnswerUsage(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cached_input_tokens=cached,
        reasoning_tokens=reasoning,
        estimated_cost_usd=None,
    )


def _parse_draft(raw_content: str) -> AnswerDraft:
    try:
        payload = orjson.loads(raw_content)
    except orjson.JSONDecodeError as exc:
        raise InvalidGeneratedAnswerError("LLM returned non-JSON") from exc

    if not isinstance(payload, dict):
        raise InvalidGeneratedAnswerError("LLM JSON is not an object")

    try:
        status = AnswerStatus(str(payload.get("status", "")))
    except ValueError as exc:
        raise InvalidGeneratedAnswerError("Invalid answer status") from exc

    blocks_raw = payload.get("blocks") or []
    if not isinstance(blocks_raw, list):
        raise InvalidGeneratedAnswerError("blocks must be a list")

    blocks: list[AnswerBlock] = []
    for item in blocks_raw:
        if not isinstance(item, dict):
            raise InvalidGeneratedAnswerError("Invalid block")
        citations = item.get("citations") or []
        if not isinstance(citations, list) or not all(isinstance(c, str) for c in citations):
            raise InvalidGeneratedAnswerError("Invalid citations")
        blocks.append(
            AnswerBlock(
                markdown=str(item.get("markdown") or ""),
                citations=list(citations),
            )
        )

    missing = payload.get("missing_context") or []
    if not isinstance(missing, list) or not all(isinstance(m, str) for m in missing):
        raise InvalidGeneratedAnswerError("Invalid missing_context")

    return AnswerDraft(status=status, blocks=blocks, missing_context=list(missing))
