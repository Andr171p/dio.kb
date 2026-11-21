from typing import Annotated

from functools import lru_cache

from fastapi import Depends

from src.api.dependencies.db import sessionmaker
from src.application.knowledge_gaps.config import KnowledgeGapsConfig
from src.infra.database.repositories import SqlAlchemyGapSignalStore, SqlAlchemyKnowledgeGapStore


@lru_cache
def get_gaps_config() -> KnowledgeGapsConfig:
    return KnowledgeGapsConfig()


GapsConfigDep = Annotated[KnowledgeGapsConfig, Depends(get_gaps_config)]


def get_gap_signal_store() -> SqlAlchemyGapSignalStore:
    return SqlAlchemyGapSignalStore(sessionmaker)


GapSignalStoreDep = Annotated[SqlAlchemyGapSignalStore, Depends(get_gap_signal_store)]


def get_knowledge_gap_store() -> SqlAlchemyKnowledgeGapStore:
    return SqlAlchemyKnowledgeGapStore(sessionmaker)


KnowledgeGapStoreDep = Annotated[SqlAlchemyKnowledgeGapStore, Depends(get_knowledge_gap_store)]
