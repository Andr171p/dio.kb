from typing import Annotated

from fastapi import Depends

from src.api.dependencies.db import DBSession
from src.application.articles.repositories import (
    ArticleQueryRepository,
    ArticleRepository,
    ArticleRevisionRepository,
)
from src.infra.database.repositories import (
    SqlAlchemyArticleQueryRepository,
    SqlAlchemyArticleRepository,
    SqlAlchemyArticleRevisionRepository,
)


def get_article_repository(session: DBSession) -> ArticleRepository:
    return SqlAlchemyArticleRepository(session)


def get_revision_repository(session: DBSession) -> ArticleRevisionRepository:
    return SqlAlchemyArticleRevisionRepository(session)


def get_article_query_repository(session: DBSession) -> ArticleQueryRepository:
    return SqlAlchemyArticleQueryRepository(session)


ArticleRepositoryDep = Annotated[ArticleRepository, Depends(get_article_repository)]
RevisionRepositoryDep = Annotated[ArticleRevisionRepository, Depends(get_revision_repository)]
ArticleQueryRepositoryDep = Annotated[ArticleQueryRepository, Depends(get_article_query_repository)]

__all__ = ["ArticleQueryRepositoryDep", "ArticleRepositoryDep", "RevisionRepositoryDep"]
