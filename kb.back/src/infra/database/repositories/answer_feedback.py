from datetime import UTC, datetime
from uuid import UUID, uuid7

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.application.answers.dtos import AnswerFeedbackRequest, AnswerFeedbackResponse
from src.infra.database.models.answers import AnswerFeedbackOrm


class SqlAlchemyAnswerFeedbackStore:
    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
        self._sessionmaker = sessionmaker

    async def upsert(
        self,
        *,
        answer_id: UUID,
        organization_id: UUID,
        actor_id: UUID,
        request: AnswerFeedbackRequest,
    ) -> AnswerFeedbackResponse:
        now = datetime.now(UTC)
        async with self._sessionmaker() as session:
            stmt = (
                insert(AnswerFeedbackOrm)
                .values(
                    id=uuid7(),
                    answer_id=answer_id,
                    organization_id=organization_id,
                    actor_id=actor_id,
                    helpful=request.helpful,
                    reason=request.reason.value if request.reason else None,
                    comment=request.comment,
                    created_at=now,
                    updated_at=now,
                )
                .on_conflict_do_update(
                    constraint="uq_answer_feedback_actor",
                    set_={
                        "helpful": request.helpful,
                        "reason": request.reason.value if request.reason else None,
                        "comment": request.comment,
                        "updated_at": now,
                    },
                )
            )
            await session.execute(stmt)
            await session.commit()

        return AnswerFeedbackResponse(
            answer_id=answer_id,
            helpful=request.helpful,
            reason=request.reason,
            comment=request.comment,
        )
