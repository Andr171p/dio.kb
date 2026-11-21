from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.application.answers.citations import validate_draft
from src.application.answers.config import AnswersConfig, AnswersProgressBackend
from src.application.answers.dtos import AnswerBlock, AnswerDraft, AnswerRequest, AnswerStatus
from src.application.answers.models import AnswerRun, AnswerRunStatus, AnswerStage
from src.application.answers.types import GeneratedAnswer
from src.application.answers.usecases import answer_question, build_execution_auth
from src.application.auth.dtos import AuthType, AuthUser
from src.application.search.dtos import SearchArticle, SearchFragment, SearchResponse, SearchResult


@pytest.mark.asyncio
async def test_answer_question_insufficient_without_sources():
    stages: list[AnswerStage] = []

    async def search(*_args, **_kwargs):
        return SearchResponse(items=[])

    async def generate(*_args, **_kwargs):
        raise AssertionError("generate must not be called")

    async def on_stage(_id, stage, _metrics):
        stages.append(stage)

    auth = AuthUser(
        id=uuid4(),
        type=AuthType.USER,
        user=AuthUser.User(id=uuid4(), email="u@example.com", organization_id=uuid4()),
    )
    answer_id = uuid4()
    response, generated = await answer_question(
        auth.user.organization_id,
        auth,
        AnswerRequest(question="Как починить принтер?"),
        answer_id=answer_id,
        search=search,
        generate=generate,
        config=AnswersConfig(progress_backend=AnswersProgressBackend.MEMORY),
        on_stage=on_stage,
    )

    assert response.status is AnswerStatus.INSUFFICIENT_EVIDENCE
    assert generated is None
    assert AnswerStage.RETRIEVAL in stages
    assert AnswerStage.CONTEXT_PREPARATION in stages
    assert AnswerStage.GENERATION not in stages


@pytest.mark.asyncio
async def test_answer_question_happy_path():
    article_id = uuid4()
    revision_id = uuid4()
    chunk_id = uuid4()
    space_id = uuid4()

    async def search(*_args, **_kwargs):
        return SearchResponse(
            items=[
                SearchResult(
                    article=SearchArticle(
                        id=article_id,
                        space_id=space_id,
                        slug="printer",
                        title="Принтер",
                        revision_id=revision_id,
                        published_at=datetime.now(UTC),
                    ),
                    score=1.0,
                    fragments=[
                        SearchFragment(
                            chunk_id=chunk_id,
                            text="Перезагрузите принтер",
                            heading_path=["Шаги"],
                            anchor="steps",
                            score=1.0,
                        )
                    ],
                )
            ]
        )

    async def generate(question, sources):
        assert question
        assert sources
        return GeneratedAnswer(
            draft=AnswerDraft(
                status=AnswerStatus.ANSWERED,
                blocks=[AnswerBlock(markdown="Перезагрузите принтер", citations=["src_1"])],
            ),
            usage=None,
            provider="aitunnel",
            model_id="gpt-4.1-nano",
            generation_ms=12,
        )

    async def on_stage(*_args, **_kwargs):
        return None

    auth = AuthUser(
        id=uuid4(),
        type=AuthType.USER,
        user=AuthUser.User(id=uuid4(), email="u@example.com", organization_id=uuid4()),
    )
    response, generated = await answer_question(
        auth.user.organization_id,
        auth,
        AnswerRequest(question="Не печатает"),
        answer_id=uuid4(),
        search=search,
        generate=generate,
        config=AnswersConfig(progress_backend=AnswersProgressBackend.MEMORY),
        on_stage=on_stage,
    )

    assert response.status is AnswerStatus.ANSWERED
    assert response.sources[0].id == "src_1"
    assert generated is not None
    validate_draft(
        AnswerDraft(status=response.status, blocks=response.blocks),
        {s.id for s in response.sources},
    )


def test_build_execution_auth_uses_roles_snapshot():
    run = AnswerRun(
        id=uuid4(),
        organization_id=uuid4(),
        principal_id=uuid4(),
        principal_type="user",
        status=AnswerRunStatus.QUEUED,
        actor_roles=["editor"],
        created_at=datetime.now(UTC),
    )
    auth = build_execution_auth(run)
    assert auth.user.id == run.principal_id
    assert "editor" in auth.user.roles
