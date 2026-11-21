from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.application.knowledge_gaps.signals import GapSignal, GapSignalKind, GapSignalSourceType
from src.infra.database.models.knowledge_gaps import GapSignalOrm


def _to_model(row: GapSignalOrm) -> GapSignal:
    return GapSignal(
        id=row.id,
        organization_id=row.organization_id,
        kind=GapSignalKind(row.kind),
        source_type=GapSignalSourceType(row.source_type),
        source_id=row.source_id,
        occurred_at=row.occurred_at,
        answer_id=row.answer_id,
        article_ids=tuple(row.article_ids or ()),
        topic_hint=row.topic_hint,
        space_id=row.space_id,
        processed_at=row.processed_at,
    )


class SqlAlchemyGapSignalStore:
    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
        self._sessionmaker = sessionmaker

    async def record(self, signal: GapSignal) -> bool:
        async with self._sessionmaker() as session:
            stmt = (
                insert(GapSignalOrm)
                .values(
                    id=signal.id,
                    organization_id=signal.organization_id,
                    kind=signal.kind.value,
                    source_type=signal.source_type.value,
                    source_id=signal.source_id,
                    occurred_at=signal.occurred_at,
                    answer_id=signal.answer_id,
                    article_ids=list(signal.article_ids) or None,
                    topic_hint=signal.topic_hint,
                    space_id=signal.space_id,
                )
                .on_conflict_do_nothing(constraint="uq_gap_signals_source")
            )
            result = await session.execute(stmt)
            await session.commit()
            return (result.rowcount or 0) > 0

    async def list_unprocessed(self, organization_id: UUID, *, limit: int) -> tuple[GapSignal, ...]:
        async with self._sessionmaker() as session:
            stmt = (
                select(GapSignalOrm)
                .where(
                    GapSignalOrm.organization_id == organization_id,
                    GapSignalOrm.processed_at.is_(None),
                )
                .order_by(GapSignalOrm.occurred_at.asc())
                .limit(limit)
            )
            rows = (await session.scalars(stmt)).all()
            return tuple(_to_model(row) for row in rows)

    async def mark_processed(self, signal_ids: tuple[UUID, ...]) -> None:
        if not signal_ids:
            return
        now = datetime.now(UTC)
        async with self._sessionmaker() as session:
            await session.execute(
                update(GapSignalOrm)
                .where(GapSignalOrm.id.in_(signal_ids), GapSignalOrm.processed_at.is_(None))
                .values(processed_at=now)
            )
            await session.commit()
