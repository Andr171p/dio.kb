from uuid import UUID

from src.application.auth.dtos import AuthUser

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
) -> AnswerFeedbackResponse:
    run = await run_store.get(answer_id, organization_id=auth.user.organization_id)
    if run is None:
        raise AnswerNotFoundError("Answer not found")
    if run.principal_id != auth.user.id:
        raise AnswerAccessDeniedError("Answer access denied")
    if run.status is not AnswerRunStatus.COMPLETED:
        raise AnswerNotReadyError("Feedback is allowed only for completed answers")

    return await feedback_store.create_or_update(
        answer_id=answer_id,
        organization_id=auth.user.organization_id,
        actor_id=auth.user.id,
        request=request,
    )
