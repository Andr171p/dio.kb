from typing import Annotated, Any

import asyncio
from collections.abc import AsyncIterator
from uuid import UUID

from fastapi import APIRouter, Header, Response, status
from sse_starlette.sse import EventSourceResponse

from src.api.dependencies.answers import (
    AnswerFeedbackStoreDep,
    AnswerProgressNotifierDep,
    AnswerRunStoreDep,
    AnswersConfigDep,
)
from src.api.dependencies.articles import ArticleQueryRepositoryDep
from src.api.dependencies.auth import CurrentUser
from src.api.dependencies.db import DBSession, OutboxDep
from src.api.dependencies.knowledge_gaps import GapsConfigDep, GapSignalStoreDep
from src.application.answers import feedback as feedback_uc
from src.application.answers import usecases as answers
from src.application.answers.config import AnswersConfig
from src.application.answers.dtos import (
    AnswerAccepted,
    AnswerFeedbackRequest,
    AnswerFeedbackResponse,
    AnswerRequest,
)
from src.application.answers.models import AnswerRun, AnswerRunStatus
from src.application.answers.repositories import AnswerRunStore
from src.infra.realtime.answer_progress import AnswerProgressNotifier

router = APIRouter(prefix="/answers", tags=["AI Answers"])

_TERMINAL = frozenset(
    {
        AnswerRunStatus.COMPLETED,
        AnswerRunStatus.FAILED,
        AnswerRunStatus.CANCELLED,
    }
)


def _sse_frame(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "event": payload["event"],
        "id": str(payload["sequence"]),
        "data": payload,
    }


async def _iter_answer_events(
    *,
    answer_id: UUID,
    organization_id: UUID,
    store: AnswerRunStore,
    notifier: AnswerProgressNotifier,
    config: AnswersConfig,
) -> AsyncIterator[dict[str, Any]]:
    subscription = notifier.subscribe(answer_id)
    subscriber = subscription.__aiter__()
    try:
        run = await store.get(answer_id, organization_id=organization_id)
        if run is None:
            return

        yield _sse_frame(answers.progress_event_from_run(run))
        if run.status in _TERMINAL:
            return

        last_sequence = run.stage_sequence
        while True:
            notified = True
            try:
                await asyncio.wait_for(subscriber.__anext__(), timeout=config.progress_heartbeat_seconds)
            except TimeoutError:
                yield {"comment": "keepalive"}
                notified = False
            except StopAsyncIteration:
                return

            run = await store.get(answer_id, organization_id=organization_id)
            if run is None:
                return
            if not notified and run.stage_sequence <= last_sequence:
                continue
            if run.stage_sequence <= last_sequence:
                continue

            last_sequence = run.stage_sequence
            yield _sse_frame(answers.progress_event_from_run(run))
            if run.status in _TERMINAL:
                return
    finally:
        await subscription.aclose()


@router.post("", status_code=status.HTTP_202_ACCEPTED, summary="Запустить AI Answers")
async def create_answer(
    dto: AnswerRequest,
    auth: CurrentUser,
    store: AnswerRunStoreDep,
    outbox: OutboxDep,
    session: DBSession,
    config: AnswersConfigDep,
    response: Response,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> AnswerAccepted:
    accepted = await answers.create_answer_run(
        auth,
        dto,
        store=store,
        outbox=outbox,
        uow=session,
        session=session,
        config=config,
        idempotency_key=idempotency_key,
    )
    response.headers["Location"] = accepted.result_url
    return accepted


@router.get("/{answer_id}", summary="Получить статус / результат AI Answers")
async def get_answer(
    answer_id: UUID,
    auth: CurrentUser,
    store: AnswerRunStoreDep,
    article_query_repository: ArticleQueryRepositoryDep,
) -> AnswerRun:
    return await answers.get_answer(
        auth,
        answer_id,
        store=store,
        article_query_repository=article_query_repository,
    )


@router.put("/{answer_id}/feedback", summary="Оценка AI-ответа")
async def put_feedback(
    answer_id: UUID,
    dto: AnswerFeedbackRequest,
    auth: CurrentUser,
    run_store: AnswerRunStoreDep,
    feedback_store: AnswerFeedbackStoreDep,
    gap_signal_store: GapSignalStoreDep,
    gaps_config: GapsConfigDep,
) -> AnswerFeedbackResponse:
    return await feedback_uc.put_answer_feedback(
        auth,
        answer_id,
        dto,
        run_store=run_store,
        feedback_store=feedback_store,
        gap_signal_store=gap_signal_store,
        gaps_config=gaps_config,
    )


@router.get("/{answer_id}/events", summary="SSE прогресс AI Answers")
async def answer_events(
    answer_id: UUID,
    auth: CurrentUser,
    store: AnswerRunStoreDep,
    article_query_repository: ArticleQueryRepositoryDep,
    notifier: AnswerProgressNotifierDep,
    config: AnswersConfigDep,
) -> EventSourceResponse:
    await answers.get_answer(
        auth,
        answer_id,
        store=store,
        article_query_repository=article_query_repository,
    )
    return EventSourceResponse(
        _iter_answer_events(
            answer_id=answer_id,
            organization_id=auth.user.organization_id,
            store=store,
            notifier=notifier,
            config=config,
        )
    )
