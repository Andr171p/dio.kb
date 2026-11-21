from typing import Annotated

from functools import lru_cache

from fastapi import Depends, Request
from redis.asyncio import Redis

from src.api.dependencies.db import sessionmaker
from src.application.answers.config import AnswersConfig
from src.infra.database.repositories import SqlAlchemyAnswerFeedbackStore, SqlAlchemyAnswerRunStore
from src.infra.realtime.answer_progress import AnswerProgressNotifier


@lru_cache
def get_answers_config() -> AnswersConfig:
    return AnswersConfig()


AnswersConfigDep = Annotated[AnswersConfig, Depends(get_answers_config)]


def get_answer_run_store() -> SqlAlchemyAnswerRunStore:
    return SqlAlchemyAnswerRunStore(sessionmaker)


AnswerRunStoreDep = Annotated[SqlAlchemyAnswerRunStore, Depends(get_answer_run_store)]


def get_answer_feedback_store() -> SqlAlchemyAnswerFeedbackStore:
    return SqlAlchemyAnswerFeedbackStore(sessionmaker)


AnswerFeedbackStoreDep = Annotated[SqlAlchemyAnswerFeedbackStore, Depends(get_answer_feedback_store)]


def get_answer_progress_notifier(request: Request) -> AnswerProgressNotifier:
    return request.app.state.answer_progress_notifier


AnswerProgressNotifierDep = Annotated[AnswerProgressNotifier, Depends(get_answer_progress_notifier)]


def get_redis(request: Request) -> Redis | None:
    return getattr(request.app.state, "redis", None)
