from typing import Annotated

from fastapi import Depends

from src.application.access.repositories import AccessGrantRepository
from src.application.articles.repositories import (
    ArticleQueryRepository,
    ArticleRepository,
    ArticleRevisionRepository,
)
from src.application.collections.repositories import CollectionPlacementRepository, CollectionRepository
from src.application.search.repositories import ArticleIndexStateRepository
from src.application.spaces.repositories import SpaceRepository
from src.infra.database.repositories import (
    SqlAlchemyAccessGrantRepository,
    SqlAlchemyArticleIndexStateRepository,
    SqlAlchemyArticleQueryRepository,
    SqlAlchemyArticleRepository,
    SqlAlchemyArticleRevisionRepository,
    SqlAlchemyCollectionPlacementRepository,
    SqlAlchemyCollectionRepository,
    SqlAlchemySpaceRepository,
)

from .db import DBSession


def get_grant_repository(session: DBSession) -> AccessGrantRepository:
    return SqlAlchemyAccessGrantRepository(session)


def get_space_repository(session: DBSession) -> SpaceRepository:
    return SqlAlchemySpaceRepository(session)


def get_collection_repository(session: DBSession) -> CollectionRepository:
    return SqlAlchemyCollectionRepository(session)


def get_placement_repository(session: DBSession) -> CollectionPlacementRepository:
    return SqlAlchemyCollectionPlacementRepository(session)


def get_article_repository(session: DBSession) -> ArticleRepository:
    return SqlAlchemyArticleRepository(session)


def get_revision_repository(session: DBSession) -> ArticleRevisionRepository:
    return SqlAlchemyArticleRevisionRepository(session)


def get_article_query_repository(session: DBSession) -> ArticleQueryRepository:
    return SqlAlchemyArticleQueryRepository(session)


def get_index_state_repository(session: DBSession) -> ArticleIndexStateRepository:
    return SqlAlchemyArticleIndexStateRepository(session)


GrantRepositoryDep = Annotated[AccessGrantRepository, Depends(get_grant_repository)]
SpaceRepositoryDep = Annotated[SpaceRepository, Depends(get_space_repository)]
CollectionRepositoryDep = Annotated[CollectionRepository, Depends(get_collection_repository)]
PlacementRepositoryDep = Annotated[CollectionPlacementRepository, Depends(get_placement_repository)]
ArticleRepositoryDep = Annotated[ArticleRepository, Depends(get_article_repository)]
RevisionRepositoryDep = Annotated[ArticleRevisionRepository, Depends(get_revision_repository)]
ArticleQueryRepositoryDep = Annotated[ArticleQueryRepository, Depends(get_article_query_repository)]
IndexStateRepositoryDep = Annotated[ArticleIndexStateRepository, Depends(get_index_state_repository)]
