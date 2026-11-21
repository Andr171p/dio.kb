from datetime import UTC, datetime
from uuid import UUID, uuid7

from src.application.access import AccessGrantRepository
from src.application.auth.dtos import AuthUser
from src.domain.knowledge_gaps.models import KnowledgeGap
from src.domain.knowledge_gaps.types import GapKind, GapStatus

from .access import ensure_gap_access, filter_readable_gaps
from .config import KnowledgeGapsConfig
from .detection import detect_organization_gaps
from .dtos import (
    DismissKnowledgeGapRequest,
    KnowledgeGapListResponse,
    KnowledgeGapResponse,
    PatchKnowledgeGapRequest,
    ResolveKnowledgeGapRequest,
)
from .exceptions import KnowledgeGapNotFoundError
from .grouping import normalize_topic_hint
from .repositories import GapSignalStore, KnowledgeGapStore
from .signals import GapSignal, GapSignalKind, GapSignalSourceType


def _to_response(gap: KnowledgeGap, *, signal_count: int = 0) -> KnowledgeGapResponse:
    return KnowledgeGapResponse(
        id=gap.id,
        organization_id=gap.organization_id,
        grouping_key=gap.grouping_key,
        title=gap.title,
        space_id=gap.space_id,
        kind=gap.kind,
        status=gap.status,
        owner_id=gap.owner_id,
        related_article_id=gap.related_article_id,
        resolution_note=gap.resolution_note,
        rationale=gap.rationale,
        signal_count=signal_count,
    )


async def record_answer_outcome_signal(
    *,
    organization_id: UUID,
    answer_id: UUID,
    answer_status: str,
    question: str | None,
    article_ids: tuple[UUID, ...] = (),
    space_id: UUID | None = None,
    signal_store: GapSignalStore,
    config: KnowledgeGapsConfig,
) -> bool:
    """Технические FAILED не создают signal."""

    kind: GapSignalKind | None = None
    if answer_status == "insufficient_evidence":
        kind = GapSignalKind.ANSWER_INSUFFICIENT
    elif answer_status == "conflicting_evidence":
        kind = GapSignalKind.SOURCES_CONFLICT

    if kind is None:
        return False

    signal = GapSignal(
        id=uuid7(),
        organization_id=organization_id,
        kind=kind,
        source_type=GapSignalSourceType.ANSWER_RUN,
        source_id=answer_id,
        occurred_at=datetime.now(UTC),
        answer_id=answer_id,
        article_ids=article_ids,
        topic_hint=normalize_topic_hint(question, max_chars=config.topic_hint_max_chars),
        space_id=space_id,
    )
    return await signal_store.record(signal)


async def record_feedback_signal(
    *,
    organization_id: UUID,
    answer_id: UUID,
    helpful: bool,
    reason: str | None,
    question: str | None,
    article_ids: tuple[UUID, ...] = (),
    space_id: UUID | None = None,
    signal_store: GapSignalStore,
    config: KnowledgeGapsConfig,
) -> bool:
    if helpful:
        return False

    kind = GapSignalKind.ANSWER_NOT_HELPFUL
    if reason == "outdated":
        kind = GapSignalKind.ARTICLE_OUTDATED

    signal = GapSignal(
        id=uuid7(),
        organization_id=organization_id,
        kind=kind,
        source_type=GapSignalSourceType.ANSWER_FEEDBACK,
        source_id=answer_id,
        occurred_at=datetime.now(UTC),
        answer_id=answer_id,
        article_ids=article_ids,
        topic_hint=normalize_topic_hint(question, max_chars=config.topic_hint_max_chars),
        space_id=space_id,
    )
    return await signal_store.record(signal)


async def run_detection(
    organization_id: UUID,
    *,
    signal_store: GapSignalStore,
    gap_store: KnowledgeGapStore,
    config: KnowledgeGapsConfig,
) -> tuple[UUID, ...]:
    return await detect_organization_gaps(
        organization_id,
        signal_store=signal_store,
        gap_store=gap_store,
        config=config,
    )


async def list_knowledge_gaps(
    auth: AuthUser,
    *,
    gap_store: KnowledgeGapStore,
    grant_repository: AccessGrantRepository,
    status: GapStatus | None = None,
    space_id: UUID | None = None,
    limit: int = 50,
) -> KnowledgeGapListResponse:
    gaps = list(
        await gap_store.list(
            auth.user.organization_id,
            status=status,
            space_id=space_id,
            limit=limit,
        )
    )
    readable = await filter_readable_gaps(auth, gaps, grant_repository=grant_repository)
    items = [_to_response(gap, signal_count=await gap_store.signal_count(gap.id)) for gap in readable]
    return KnowledgeGapListResponse(items=items)


async def get_knowledge_gap(
    auth: AuthUser,
    gap_id: UUID,
    *,
    gap_store: KnowledgeGapStore,
    grant_repository: AccessGrantRepository,
) -> KnowledgeGapResponse:
    gap = await gap_store.read(gap_id, organization_id=auth.user.organization_id)
    if gap is None:
        raise KnowledgeGapNotFoundError("Knowledge gap not found")
    await ensure_gap_access(auth, gap, grant_repository=grant_repository)
    return _to_response(gap, signal_count=await gap_store.signal_count(gap.id))


async def patch_knowledge_gap(
    auth: AuthUser,
    gap_id: UUID,
    dto: PatchKnowledgeGapRequest,
    *,
    gap_store: KnowledgeGapStore,
    grant_repository: AccessGrantRepository,
) -> KnowledgeGapResponse:
    gap = await gap_store.read(gap_id, organization_id=auth.user.organization_id)
    if gap is None:
        raise KnowledgeGapNotFoundError("Knowledge gap not found")
    await ensure_gap_access(auth, gap, grant_repository=grant_repository)

    if dto.kind is not None:
        gap.triage(dto.kind, article_id=dto.related_article_id)
    elif dto.related_article_id is not None and gap.kind is not GapKind.NEEDS_TRIAGE:
        gap.related_article_id = dto.related_article_id

    if dto.owner_id is not None:
        gap.assign(dto.owner_id)

    await gap_store.save(gap)
    return _to_response(gap, signal_count=await gap_store.signal_count(gap.id))


async def start_knowledge_gap(
    auth: AuthUser,
    gap_id: UUID,
    *,
    gap_store: KnowledgeGapStore,
    grant_repository: AccessGrantRepository,
) -> KnowledgeGapResponse:
    gap = await gap_store.read(gap_id, organization_id=auth.user.organization_id)
    if gap is None:
        raise KnowledgeGapNotFoundError("Knowledge gap not found")
    await ensure_gap_access(auth, gap, grant_repository=grant_repository)
    gap.start()
    await gap_store.save(gap)
    return _to_response(gap, signal_count=await gap_store.signal_count(gap.id))


async def resolve_knowledge_gap(
    auth: AuthUser,
    gap_id: UUID,
    dto: ResolveKnowledgeGapRequest,
    *,
    gap_store: KnowledgeGapStore,
    grant_repository: AccessGrantRepository,
) -> KnowledgeGapResponse:
    gap = await gap_store.read(gap_id, organization_id=auth.user.organization_id)
    if gap is None:
        raise KnowledgeGapNotFoundError("Knowledge gap not found")
    await ensure_gap_access(auth, gap, grant_repository=grant_repository)
    gap.resolve(dto.note)
    await gap_store.save(gap)
    return _to_response(gap, signal_count=await gap_store.signal_count(gap.id))


async def dismiss_knowledge_gap(
    auth: AuthUser,
    gap_id: UUID,
    dto: DismissKnowledgeGapRequest,
    *,
    gap_store: KnowledgeGapStore,
    grant_repository: AccessGrantRepository,
) -> KnowledgeGapResponse:
    gap = await gap_store.read(gap_id, organization_id=auth.user.organization_id)
    if gap is None:
        raise KnowledgeGapNotFoundError("Knowledge gap not found")
    await ensure_gap_access(auth, gap, grant_repository=grant_repository)
    gap.dismiss(dto.reason)
    await gap_store.save(gap)
    return _to_response(gap, signal_count=await gap_store.signal_count(gap.id))


async def reopen_knowledge_gap(
    auth: AuthUser,
    gap_id: UUID,
    *,
    gap_store: KnowledgeGapStore,
    grant_repository: AccessGrantRepository,
) -> KnowledgeGapResponse:
    gap = await gap_store.read(gap_id, organization_id=auth.user.organization_id)
    if gap is None:
        raise KnowledgeGapNotFoundError("Knowledge gap not found")
    await ensure_gap_access(auth, gap, grant_repository=grant_repository)
    gap.reopen()
    await gap_store.save(gap)
    return _to_response(gap, signal_count=await gap_store.signal_count(gap.id))
