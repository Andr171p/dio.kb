from datetime import UTC, datetime
from uuid import UUID, uuid7

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.application.knowledge_gaps.dtos import GapCandidate
from src.domain.knowledge_gaps.models import KnowledgeGap
from src.domain.knowledge_gaps.types import GapKind, GapStatus
from src.infra.database.models.knowledge_gaps import GapSignalOrm, KnowledgeGapOrm, KnowledgeGapSignalOrm


def _to_model(row: KnowledgeGapOrm) -> KnowledgeGap:
    return KnowledgeGap(
        id=row.id,
        created_at=row.created_at,
        updated_at=row.updated_at,
        organization_id=row.organization_id,
        grouping_key=row.grouping_key,
        title=row.title,
        space_id=row.space_id,
        kind=GapKind(row.kind),
        status=GapStatus(row.status),
        owner_id=row.owner_id,
        related_article_id=row.related_article_id,
        resolution_note=row.resolution_note,
        rationale=row.rationale,
    )


class SqlAlchemyKnowledgeGapStore:
    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
        self._sessionmaker = sessionmaker

    async def read(self, gap_id: UUID, *, organization_id: UUID) -> KnowledgeGap | None:
        async with self._sessionmaker() as session:
            stmt = select(KnowledgeGapOrm).where(
                KnowledgeGapOrm.id == gap_id,
                KnowledgeGapOrm.organization_id == organization_id,
            )
            row = await session.scalar(stmt)
            return _to_model(row) if row else None

    async def save(self, gap: KnowledgeGap) -> None:
        async with self._sessionmaker() as session:
            row = await session.get(KnowledgeGapOrm, gap.id)
            if row is None or row.organization_id != gap.organization_id:
                raise ValueError("Knowledge gap not found")
            row.title = gap.title
            row.space_id = gap.space_id
            row.kind = gap.kind.value
            row.status = gap.status.value
            row.owner_id = gap.owner_id
            row.related_article_id = gap.related_article_id
            row.resolution_note = gap.resolution_note
            row.rationale = gap.rationale
            row.updated_at = gap.updated_at
            row.version = row.version + 1
            await session.commit()

    async def list(
        self,
        organization_id: UUID,
        *,
        status: GapStatus | None = None,
        space_id: UUID | None = None,
        owner_id: UUID | None = None,
        limit: int = 50,
    ) -> tuple[KnowledgeGap, ...]:
        async with self._sessionmaker() as session:
            stmt = select(KnowledgeGapOrm).where(KnowledgeGapOrm.organization_id == organization_id)
            if status is not None:
                stmt = stmt.where(KnowledgeGapOrm.status == status.value)
            if space_id is not None:
                stmt = stmt.where(KnowledgeGapOrm.space_id == space_id)
            if owner_id is not None:
                stmt = stmt.where(KnowledgeGapOrm.owner_id == owner_id)
            stmt = stmt.order_by(KnowledgeGapOrm.updated_at.desc()).limit(limit)
            rows = (await session.scalars(stmt)).all()
            return tuple(_to_model(row) for row in rows)

    async def upsert_candidate(self, candidate: GapCandidate) -> UUID:
        now = datetime.now(UTC)
        async with self._sessionmaker() as session:
            existing = await session.scalar(
                select(KnowledgeGapOrm).where(
                    KnowledgeGapOrm.organization_id == candidate.organization_id,
                    KnowledgeGapOrm.grouping_key == candidate.grouping_key,
                )
            )
            if existing is not None:
                if existing.status in (GapStatus.RESOLVED.value, GapStatus.DISMISSED.value):
                    existing.status = GapStatus.OPEN.value
                    existing.resolution_note = None
                if existing.kind == GapKind.NEEDS_TRIAGE.value:
                    existing.kind = candidate.suggested_kind.value
                if existing.space_id is None and candidate.space_id is not None:
                    existing.space_id = candidate.space_id
                if existing.related_article_id is None and candidate.related_article_ids:
                    existing.related_article_id = candidate.related_article_ids[0]
                existing.rationale = candidate.rationale or existing.rationale
                existing.title = candidate.title or existing.title
                existing.updated_at = now
                existing.version = existing.version + 1
                await session.commit()
                return existing.id

            gap_id = uuid7()
            session.add(
                KnowledgeGapOrm(
                    id=gap_id,
                    organization_id=candidate.organization_id,
                    space_id=candidate.space_id,
                    grouping_key=candidate.grouping_key,
                    title=candidate.title,
                    kind=candidate.suggested_kind.value,
                    status=GapStatus.OPEN.value,
                    related_article_id=candidate.related_article_ids[0] if candidate.related_article_ids else None,
                    rationale=candidate.rationale,
                    created_at=now,
                    updated_at=now,
                )
            )
            await session.commit()
            return gap_id

    async def link_signals(self, gap_id: UUID, signal_ids: tuple[UUID, ...]) -> None:
        if not signal_ids:
            return
        async with self._sessionmaker() as session:
            gap = await session.get(KnowledgeGapOrm, gap_id)
            if gap is None:
                raise ValueError("Knowledge gap not found")

            signals = (
                await session.scalars(
                    select(GapSignalOrm).where(
                        GapSignalOrm.id.in_(signal_ids),
                        GapSignalOrm.organization_id == gap.organization_id,
                    )
                )
            ).all()
            for signal in signals:
                stmt = (
                    insert(KnowledgeGapSignalOrm)
                    .values(
                        gap_id=gap_id,
                        signal_id=signal.id,
                        organization_id=gap.organization_id,
                    )
                    .on_conflict_do_nothing(constraint="uq_knowledge_gap_signals")
                )
                await session.execute(stmt)
            await session.commit()

    async def signal_count(self, gap_id: UUID) -> int:
        async with self._sessionmaker() as session:
            count = await session.scalar(
                select(func.count())
                .select_from(KnowledgeGapSignalOrm)
                .where(KnowledgeGapSignalOrm.gap_id == gap_id)
            )
            return int(count or 0)
