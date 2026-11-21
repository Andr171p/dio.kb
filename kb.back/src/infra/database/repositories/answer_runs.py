from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import and_, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.application.answers.dtos import AnswerResponse, AnswerStatus
from src.application.answers.models import AnswerRun, AnswerRunStatus, AnswerStage, AnswerUsage
from src.infra.database.models.answers import AnswerRunOrm


def _to_model(row: AnswerRunOrm) -> AnswerRun:
    response = None
    if row.response is not None:
        response = AnswerResponse.model_validate(row.response)

    usage = None
    if row.usage is not None:
        usage = AnswerUsage.model_validate(row.usage)

    return AnswerRun(
        id=row.id,
        organization_id=row.organization_id,
        principal_id=row.principal_id,
        principal_type=row.principal_type,
        status=AnswerRunStatus(row.status),
        stage=AnswerStage(row.stage) if row.stage else None,
        stage_sequence=row.stage_sequence,
        question=row.question,
        space_ids=list(row.space_ids) if row.space_ids is not None else None,
        actor_roles=list(row.actor_roles or []),
        answer_status=AnswerStatus(row.answer_status) if row.answer_status else None,
        response=response,
        provider=row.provider,
        model_id=row.model_id,
        prompt_version=row.prompt_version,
        retrieval_version=row.retrieval_version,
        usage=usage,
        results_count=row.results_count,
        sources_count=row.sources_count,
        latency_ms=row.latency_ms,
        error_code=row.error_code,
        idempotency_key=row.idempotency_key,
        created_at=row.created_at,
        started_at=row.started_at,
        completed_at=row.completed_at,
    )


class SqlAlchemyAnswerRunStore:
    """Store с короткими транзакциями через sessionmaker (API и worker)."""

    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
        self._sessionmaker = sessionmaker

    def _orm(self, run: AnswerRun) -> AnswerRunOrm:
        return AnswerRunOrm(
            id=run.id,
            organization_id=run.organization_id,
            principal_id=run.principal_id,
            principal_type=run.principal_type,
            status=run.status.value,
            stage=run.stage.value if run.stage else None,
            stage_sequence=run.stage_sequence,
            question=run.question,
            space_ids=run.space_ids,
            actor_roles=run.actor_roles,
            answer_status=run.answer_status.value if run.answer_status else None,
            response=run.response.model_dump(mode="json") if run.response else None,
            provider=run.provider,
            model_id=run.model_id,
            prompt_version=run.prompt_version,
            retrieval_version=run.retrieval_version,
            usage=run.usage.model_dump(mode="json") if run.usage else None,
            results_count=run.results_count,
            sources_count=run.sources_count,
            latency_ms=run.latency_ms,
            error_code=run.error_code,
            idempotency_key=run.idempotency_key,
            created_at=run.created_at,
            started_at=run.started_at,
            completed_at=run.completed_at,
        )

    async def create(self, run: AnswerRun, *, session: AsyncSession | None = None) -> None:
        """Если передан ``session`` — только add (commit с outbox снаружи)."""

        if session is not None:
            session.add(self._orm(run))
            return

        async with self._sessionmaker() as own:
            own.add(self._orm(run))
            await own.commit()

    async def get_by_idempotency(
        self,
        *,
        organization_id: UUID,
        principal_id: UUID,
        idempotency_key: str,
    ) -> AnswerRun | None:
        async with self._sessionmaker() as session:
            stmt = select(AnswerRunOrm).where(
                AnswerRunOrm.organization_id == organization_id,
                AnswerRunOrm.principal_id == principal_id,
                AnswerRunOrm.idempotency_key == idempotency_key,
            )
            row = await session.scalar(stmt)
            return _to_model(row) if row else None

    async def claim(self, run_id: UUID, *, owner: str, lease_seconds: int) -> AnswerRun | None:
        now = datetime.now(UTC)
        expires = now + timedelta(seconds=lease_seconds)

        async with self._sessionmaker() as session:
            stmt = (
                update(AnswerRunOrm)
                .where(
                    AnswerRunOrm.id == run_id,
                    or_(
                        AnswerRunOrm.status == AnswerRunStatus.QUEUED.value,
                        and_(
                            AnswerRunOrm.status == AnswerRunStatus.RUNNING.value,
                            or_(
                                AnswerRunOrm.lease_expires_at.is_(None),
                                AnswerRunOrm.lease_expires_at < now,
                            ),
                        ),
                    ),
                )
                .values(
                    status=AnswerRunStatus.RUNNING.value,
                    started_at=now,
                    lease_owner=owner,
                    lease_expires_at=expires,
                    stage_sequence=AnswerRunOrm.stage_sequence + 1,
                )
                .returning(AnswerRunOrm)
            )
            row = await session.scalar(stmt)
            await session.commit()
            return _to_model(row) if row else None

    async def update_stage(
        self,
        run_id: UUID,
        stage: AnswerStage,
        *,
        metrics: dict[str, int],
        owner: str,
    ) -> int:
        values: dict[str, object] = {
            "stage": stage.value,
            "stage_sequence": AnswerRunOrm.stage_sequence + 1,
            "lease_expires_at": datetime.now(UTC) + timedelta(seconds=120),
        }
        if "results_count" in metrics:
            values["results_count"] = metrics["results_count"]
        if "sources_count" in metrics:
            values["sources_count"] = metrics["sources_count"]

        async with self._sessionmaker() as session:
            stmt = (
                update(AnswerRunOrm)
                .where(
                    AnswerRunOrm.id == run_id,
                    AnswerRunOrm.status == AnswerRunStatus.RUNNING.value,
                    AnswerRunOrm.lease_owner == owner,
                )
                .values(**values)
                .returning(AnswerRunOrm.stage_sequence)
            )
            sequence = await session.scalar(stmt)
            await session.commit()
            if sequence is None:
                raise RuntimeError("Failed to update answer stage: lease lost")
            return int(sequence)

    async def complete(
        self,
        run_id: UUID,
        *,
        response: AnswerResponse,
        usage: AnswerUsage | None,
        metadata: dict[str, object],
        owner: str,
    ) -> None:
        now = datetime.now(UTC)
        async with self._sessionmaker() as session:
            row = await session.get(AnswerRunOrm, run_id)
            if row is None or row.lease_owner != owner or row.status != AnswerRunStatus.RUNNING.value:
                raise RuntimeError("Cannot complete answer run: lease mismatch")

            started = row.started_at or row.created_at
            latency = int((now - started).total_seconds() * 1000)

            row.status = AnswerRunStatus.COMPLETED.value
            row.answer_status = response.status.value
            row.response = response.model_dump(mode="json")
            row.usage = usage.model_dump(mode="json") if usage else None
            row.estimated_cost_usd = usage.estimated_cost_usd if usage else None
            if metadata.get("provider"):
                row.provider = str(metadata["provider"])
            if metadata.get("model_id"):
                row.model_id = str(metadata["model_id"])
            if metadata.get("prompt_version"):
                row.prompt_version = str(metadata["prompt_version"])
            if metadata.get("retrieval_version"):
                row.retrieval_version = str(metadata["retrieval_version"])
            row.metrics = {
                **(row.metrics or {}),
                **{k: v for k, v in metadata.items() if isinstance(v, int | str)},
            }
            row.latency_ms = latency
            row.completed_at = now
            row.lease_owner = None
            row.lease_expires_at = None
            row.stage_sequence = row.stage_sequence + 1
            row.error_code = None
            await session.commit()

    async def fail(self, run_id: UUID, *, code: str, owner: str | None = None) -> None:
        now = datetime.now(UTC)
        async with self._sessionmaker() as session:
            conditions = [
                AnswerRunOrm.id == run_id,
                AnswerRunOrm.status.in_(
                    [AnswerRunStatus.QUEUED.value, AnswerRunStatus.RUNNING.value]
                ),
            ]
            if owner is not None:
                conditions.append(
                    or_(AnswerRunOrm.lease_owner == owner, AnswerRunOrm.lease_owner.is_(None))
                )

            stmt = (
                update(AnswerRunOrm)
                .where(*conditions)
                .values(
                    status=AnswerRunStatus.FAILED.value,
                    error_code=code,
                    completed_at=now,
                    lease_owner=None,
                    lease_expires_at=None,
                    stage_sequence=AnswerRunOrm.stage_sequence + 1,
                )
            )
            await session.execute(stmt)
            await session.commit()

    async def get(self, run_id: UUID, *, organization_id: UUID) -> AnswerRun | None:
        async with self._sessionmaker() as session:
            stmt = select(AnswerRunOrm).where(
                AnswerRunOrm.id == run_id,
                AnswerRunOrm.organization_id == organization_id,
            )
            row = await session.scalar(stmt)
            return _to_model(row) if row else None
