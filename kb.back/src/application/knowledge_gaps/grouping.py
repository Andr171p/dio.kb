import hashlib
import re
from collections.abc import Sequence

from .signals import GapSignal, GapSignalKind

_WHITESPACE = re.compile(r"\s+")
_NON_WORD = re.compile(r"[^\w\s\-]+", re.UNICODE)


def normalize_topic_hint(text: str | None, *, max_chars: int = 120) -> str | None:
    if text is None:
        return None
    cleaned = _NON_WORD.sub(" ", text.lower())
    cleaned = _WHITESPACE.sub(" ", cleaned).strip()
    if not cleaned:
        return None
    return cleaned[:max_chars]


def grouping_key_for(signal: GapSignal) -> str:
    """Стабильный tenant-local ключ без сырого текста вопроса."""

    hint = normalize_topic_hint(signal.topic_hint) or "unknown"
    digest = hashlib.sha256(f"{signal.kind.value}:{hint}".encode()).hexdigest()[:24]
    return f"{signal.kind.value}:{digest}"


def group_signals(signals: Sequence[GapSignal]) -> list[list[GapSignal]]:
    buckets: dict[str, list[GapSignal]] = {}
    for signal in signals:
        key = grouping_key_for(signal)
        buckets.setdefault(key, []).append(signal)
    return list(buckets.values())


def suggested_kind_for(group: Sequence[GapSignal]):
    from src.domain.knowledge_gaps.types import GapKind

    kinds = {signal.kind for signal in group}
    if GapSignalKind.SOURCES_CONFLICT in kinds:
        return GapKind.CONFLICTING_CONTENT
    if GapSignalKind.ARTICLE_OUTDATED in kinds:
        return GapKind.OUTDATED_CONTENT
    if kinds == {GapSignalKind.ANSWER_NOT_HELPFUL}:
        return GapKind.NEEDS_TRIAGE
    if GapSignalKind.ANSWER_INSUFFICIENT in kinds:
        # Не доказываем MISSING_CONTENT одним insufficient.
        return GapKind.NEEDS_TRIAGE
    return GapKind.NEEDS_TRIAGE
