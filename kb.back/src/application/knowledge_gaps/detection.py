from collections.abc import Awaitable, Callable, Sequence
from uuid import UUID

from .config import KnowledgeGapsConfig
from .dtos import GapCandidate
from .grouping import group_signals, grouping_key_for, normalize_topic_hint, suggested_kind_for
from .signals import GapSignal

type AssessGap = Callable[[Sequence[GapSignal]], Awaitable[GapCandidate | None]]
type SaveGapCandidate = Callable[[GapCandidate], Awaitable[UUID]]


def build_candidate(group: Sequence[GapSignal], *, config: KnowledgeGapsConfig) -> GapCandidate | None:
    if len(group) < config.min_signals:
        return None

    first = group[0]
    organization_id = first.organization_id
    if any(signal.organization_id != organization_id for signal in group):
        raise ValueError("Signals from different organizations cannot be grouped")

    hint = normalize_topic_hint(first.topic_hint, max_chars=config.topic_hint_max_chars)
    title = (hint or "Повторяющаяся проблема знаний").capitalize()
    article_ids = tuple(dict.fromkeys(aid for signal in group for aid in signal.article_ids))
    space_ids = {signal.space_id for signal in group if signal.space_id is not None}
    space_id = next(iter(space_ids)) if len(space_ids) == 1 else None

    kind = suggested_kind_for(group)
    rationale = f"Grouped {len(group)} signal(s) of kind {[s.kind.value for s in group]}"

    return GapCandidate(
        organization_id=organization_id,
        grouping_key=grouping_key_for(first),
        title=title,
        suggested_kind=kind,
        signal_ids=tuple(signal.id for signal in group),
        related_article_ids=article_ids,
        rationale=rationale,
        space_id=space_id,
    )


async def assess_group_rules(group: Sequence[GapSignal], *, config: KnowledgeGapsConfig) -> GapCandidate | None:
    """Дешёвая rule-based оценка без LLM."""

    return build_candidate(group, config=config)


async def detect_gaps(
    groups: Sequence[Sequence[GapSignal]],
    *,
    assess: AssessGap,
    save: SaveGapCandidate,
) -> tuple[UUID, ...]:
    created_or_updated: list[UUID] = []
    for group in groups:
        if not group:
            continue
        candidate = await assess(group)
        if candidate is None:
            continue
        created_or_updated.append(await save(candidate))
    return tuple(created_or_updated)


async def detect_organization_gaps(
    organization_id: UUID,
    *,
    signal_store,
    gap_store,
    config: KnowledgeGapsConfig,
) -> tuple[UUID, ...]:
    signals = await signal_store.list_unprocessed(organization_id, limit=config.batch_limit)
    if not signals:
        return ()

    groups = group_signals(signals)

    async def assess(group: Sequence[GapSignal]) -> GapCandidate | None:
        return await assess_group_rules(group, config=config)

    async def save(candidate: GapCandidate) -> UUID:
        gap_id = await gap_store.upsert_candidate(candidate)
        await gap_store.link_signals(gap_id, candidate.signal_ids)
        return gap_id

    gap_ids = await detect_gaps(groups, assess=assess, save=save)
    processed = tuple(signal.id for group in groups for signal in group if len(group) >= config.min_signals)
    if processed:
        await signal_store.mark_processed(processed)
    return gap_ids
