from uuid import UUID

from src.application.auth.dtos import AuthUser
from src.application.knowledge_gaps.config import KnowledgeGapsConfig
from src.application.knowledge_gaps.repositories import GapSignalStore

from .dtos import AnswerFeedbackRequest, AnswerFeedbackResponse
from .exceptions import AnswerAccessDeniedError, AnswerNotFoundError, AnswerNotReadyError
from .models import AnswerRunStatus
from .repositories import AnswerFeedbackStore, AnswerRunStore


async def put_answer_feedback(
    auth: AuthUser,
    answer_id: UUID,
    request: AnswerFeedbackRequest,
    *,
    run_store: AnswerRunStore,
    feedback_store: AnswerFeedbackStore,
    gap_signal_store: GapSignalStore | None = None,
    gaps_config: KnowledgeGapsConfig | None = None,
) -> AnswerFeedbackResponse:
    run = await run_store.get(answer_id, organization_id=auth.user.organization_id)
    if run is None:
        raise AnswerNotFoundError("Answer not found")
    if run.principal_id != auth.user.id:
        raise AnswerAccessDeniedError("Answer access denied")
    if run.status is not AnswerRunStatus.COMPLETED:
        raise AnswerNotReadyError("Feedback is allowed only for completed answers")

    result = await feedback_store.create_or_update(
        answer_id=answer_id,
        organization_id=auth.user.organization_id,
        actor_id=auth.user.id,
        request=request,
    )

    if gap_signal_store is not None and gaps_config is not None:
        from src.application.knowledge_gaps import usecases as gaps

        article_ids = tuple(source.article_id for source in run.response.sources) if run.response else ()
        space_id = None
        if run.space_ids and len(run.space_ids) == 1:
            space_id = run.space_ids[0]

        await gaps.record_feedback_signal(
            organization_id=run.organization_id,
            answer_id=answer_id,
            helpful=request.helpful,
            reason=request.reason.value if request.reason else None,
            question=run.question,
            article_ids=article_ids,
            space_id=space_id,
            signal_store=gap_signal_store,
            config=gaps_config,
        )

    return result
