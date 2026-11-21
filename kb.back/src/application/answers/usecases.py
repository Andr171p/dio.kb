import asyncio
from collections.abc import Sequence
from datetime import UTC, datetime
from functools import partial
from uuid import UUID, uuid7

from ddf.application.events import serialize_event
from ddf.application.outbox import OutboxMessage, OutboxStore
from ddf.application.uow import UnitOfWork

from src.application.articles.repositories import ArticleQueryRepository
from src.application.auth.dtos import AuthType, AuthUser
from src.application.search.dtos import SearchRequest

from .citations import make_insufficient_evidence_response, make_response, validate_draft
from .config import AnswersConfig, AnswersPrivacyMode
from .dtos import AnswerAccepted, AnswerRequest, AnswerResponse, AnswerSource
from .events import GenerateAnswerRequested
from .evidence import build_sources
from .exceptions import (
    AnswerAccessChangedError,
    AnswerAccessDeniedError,
    AnswerNotFoundError,
    InvalidGeneratedAnswerError,
)
from .models import AnswerRun, AnswerRunStatus, AnswerStage
from .repositories import AnswerRunStore
from .types import GenerateAnswer, NotifyAnswerProgress, ReportProgress, SearchForAnswer
from .urls import build_source_url


def build_execution_auth(run: AnswerRun) -> AuthUser:
    """Строит AuthUser для worker из сохранённых principal + roles snapshot.

    Авторитетная проверка доступа — актуальные AccessGrants в PostgreSQL
    (через ``search_articles`` / ``find_readable_published``), а не «замороженные» статьи.
    """

    return AuthUser(
        id=run.principal_id,
        type=AuthType.USER,
        user=AuthUser.User(
            id=run.principal_id,
            email=f"answers-{run.principal_id}@example.com",
            organization_id=run.organization_id,
            roles=frozenset(run.actor_roles),
        ),
    )


def _api_paths(run_id: UUID) -> tuple[str, str]:
    base = f"/api/user/v1/answers/{run_id}"
    return f"{base}/events", base


async def create_answer_run(
    auth: AuthUser,
    request: AnswerRequest,
    *,
    store: AnswerRunStore,
    outbox: OutboxStore,
    uow: UnitOfWork,
    session: object,
    config: AnswersConfig,
    idempotency_key: str | None = None,
) -> AnswerAccepted:
    if idempotency_key:
        existing = await store.get_by_idempotency(
            organization_id=auth.user.organization_id,
            principal_id=auth.user.id,
            idempotency_key=idempotency_key,
        )
        if existing is not None:
            events_url, result_url = _api_paths(existing.id)
            return AnswerAccepted(
                id=existing.id,
                status=existing.status.value,
                events_url=events_url,
                result_url=result_url,
            )

    run_id = uuid7()
    now = datetime.now(UTC)

    run = AnswerRun(
        id=run_id,
        organization_id=auth.user.organization_id,
        principal_id=auth.user.id,
        principal_type="user",
        status=AnswerRunStatus.QUEUED,
        question=request.question,
        space_ids=request.space_ids,
        actor_roles=sorted(auth.user.roles),
        idempotency_key=idempotency_key,
        prompt_version=config.prompt_version,
        retrieval_version=config.retrieval_version,
        created_at=now,
    )

    await store.create(run, session=session)

    event = GenerateAnswerRequested(
        organization_id=auth.user.organization_id,
        run_id=run_id,
    )
    await outbox.save_all(
        [
            OutboxMessage(
                type=event.event_type,
                occurred_on=event.occurred_on,
                payload=serialize_event(event),
            )
        ]
    )
    await uow.commit()

    events_url, result_url = _api_paths(run_id)
    return AnswerAccepted(
        id=run_id,
        status=AnswerRunStatus.QUEUED.value,
        events_url=events_url,
        result_url=result_url,
    )


async def answer_question(
    organization_id: UUID,
    auth: AuthUser,
    request: AnswerRequest,
    *,
    answer_id: UUID,
    search: SearchForAnswer,
    generate: GenerateAnswer,
    config: AnswersConfig,
    on_stage: ReportProgress,
) -> tuple[AnswerResponse, object | None]:
    await on_stage(answer_id, AnswerStage.RETRIEVAL, {})
    results = await search(
        organization_id,
        auth,
        SearchRequest(
            query=request.question[:500],
            space_ids=request.space_ids,
            limit=config.candidates_limit,
        ),
    )

    await on_stage(answer_id, AnswerStage.CONTEXT_PREPARATION, {"results_count": len(results.items)})
    build_url = partial(build_source_url, base_url=config.public_base_url)
    sources = build_sources(
        results,
        build_url=build_url,
        limit=config.max_sources,
        max_chars=config.max_excerpt_chars,
    )
    if not sources:
        return make_insufficient_evidence_response(answer_id), None

    await on_stage(answer_id, AnswerStage.GENERATION, {"sources_count": len(sources)})
    generated = await generate(request.question, sources)

    await on_stage(answer_id, AnswerStage.VALIDATION, {})
    used_ids = validate_draft(generated.draft, {source.id for source in sources})
    response = make_response(answer_id, generated.draft, sources, used_ids)
    return response, generated


async def ensure_sources_readable(
    organization_id: UUID,
    auth: AuthUser,
    sources: Sequence[AnswerSource],
    *,
    article_query_repository: ArticleQueryRepository,
) -> None:
    if not sources:
        return

    from src.application.access import build_subjects_from_auth
    from src.application.search.access import PUBLIC_SUBJECT

    article_ids = list({source.article_id for source in sources})
    readable = {
        article.id: article
        for article in await article_query_repository.find_readable_published(
            organization_id,
            article_ids,
            subjects={PUBLIC_SUBJECT} | build_subjects_from_auth(auth),
        )
    }

    for source in sources:
        article = readable.get(source.article_id)
        if article is None or article.published_revision_id != source.revision_id:
            raise AnswerAccessChangedError("Source access revoked or publication changed")


async def execute_answer_run(
    run_id: UUID,
    *,
    store: AnswerRunStore,
    search: SearchForAnswer,
    generate: GenerateAnswer,
    article_query_repository: ArticleQueryRepository,
    config: AnswersConfig,
    notify: NotifyAnswerProgress,
    owner: str,
) -> None:
    claimed = await store.claim(run_id, owner=owner, lease_seconds=config.lease_seconds)
    if claimed is None:
        return

    await notify(run_id)

    async def on_stage(_run_id: UUID, stage: AnswerStage, metrics: dict[str, int]) -> None:
        await store.update_stage(run_id, stage, metrics=metrics, owner=owner)
        await notify(run_id)

    if not claimed.question:
        await store.fail(run_id, code="MISSING_QUESTION", owner=owner)
        await notify(run_id)
        return

    auth = build_execution_auth(claimed)
    request = AnswerRequest(question=claimed.question, space_ids=claimed.space_ids)

    try:
        async with asyncio.timeout(config.total_timeout):
            response, generated = await answer_question(
                claimed.organization_id,
                auth,
                request,
                answer_id=run_id,
                search=search,
                generate=generate,
                config=config,
                on_stage=on_stage,
            )
            await ensure_sources_readable(
                claimed.organization_id,
                auth,
                response.sources,
                article_query_repository=article_query_repository,
            )
    except TimeoutError:
        await store.fail(run_id, code="TOTAL_TIMEOUT", owner=owner)
        await notify(run_id)
        return
    except AnswerAccessChangedError:
        await store.fail(run_id, code="ACCESS_CHANGED", owner=owner)
        await notify(run_id)
        return
    except InvalidGeneratedAnswerError:
        await store.fail(run_id, code="LLM_INVALID_OUTPUT", owner=owner)
        await notify(run_id)
        return
    except Exception:
        await store.fail(run_id, code="EXECUTION_FAILED", owner=owner)
        await notify(run_id)
        raise

    metadata: dict[str, object] = {
        "prompt_version": config.prompt_version,
        "retrieval_version": config.retrieval_version,
    }
    usage = None
    if generated is not None:
        usage = generated.usage
        metadata["provider"] = generated.provider
        metadata["model_id"] = generated.model_id
        metadata["generation_ms"] = generated.generation_ms

    if config.privacy_mode is AnswersPrivacyMode.METADATA_ONLY:
        response = response.model_copy(
            update={
                "blocks": [],
                "sources": [
                    source.model_copy(update={"excerpt": "", "title": ""}) for source in response.sources
                ],
            }
        )

    await store.complete(
        run_id,
        response=response,
        usage=usage,
        metadata=metadata,
        owner=owner,
    )
    await notify(run_id)


async def get_answer(
    auth: AuthUser,
    run_id: UUID,
    *,
    store: AnswerRunStore,
    article_query_repository: ArticleQueryRepository,
) -> AnswerRun:
    run = await store.get(run_id, organization_id=auth.user.organization_id)
    if run is None:
        raise AnswerNotFoundError("Answer not found")

    if run.principal_id != auth.user.id and not auth.is_admin:
        raise AnswerAccessDeniedError("Answer access denied")

    if run.status is AnswerRunStatus.COMPLETED and run.response is not None:
        try:
            await ensure_sources_readable(
                run.organization_id,
                auth,
                run.response.sources,
                article_query_repository=article_query_repository,
            )
        except AnswerAccessChangedError:
            raise AnswerAccessDeniedError("Source access changed") from None

    return run


def progress_event_from_run(run: AnswerRun) -> dict[str, object]:
    event_name = "answer.snapshot"
    if run.status is AnswerRunStatus.QUEUED:
        event_name = "answer.queued"
    elif run.status is AnswerRunStatus.FAILED:
        event_name = "answer.failed"
    elif run.status is AnswerRunStatus.COMPLETED:
        event_name = "answer.completed"
    elif run.status is AnswerRunStatus.CANCELLED:
        event_name = "answer.cancelled"
    elif run.stage is AnswerStage.RETRIEVAL:
        event_name = "retrieval.started" if run.results_count is None else "retrieval.completed"
    elif run.stage is AnswerStage.CONTEXT_PREPARATION:
        event_name = "context.prepared"
    elif run.stage is AnswerStage.GENERATION:
        event_name = "generation.started"
    elif run.stage is AnswerStage.VALIDATION:
        event_name = "validation.started"

    return {
        "answerId": str(run.id),
        "sequence": run.stage_sequence,
        "event": event_name,
        "occurredAt": datetime.now(UTC).isoformat(),
        "status": run.status.value,
        "stage": run.stage.value if run.stage else None,
        "resultsCount": run.results_count,
        "sourcesCount": run.sources_count,
        "errorCode": run.error_code,
    }


__all__ = [
    "answer_question",
    "build_execution_auth",
    "create_answer_run",
    "ensure_sources_readable",
    "execute_answer_run",
    "get_answer",
    "progress_event_from_run",
]
