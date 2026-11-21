from typing import Annotated

from contextvars import ContextVar

from mcp.server import ServerRequestContext
from mcp.server.context import CallNext, HandlerResult
from mcp.server.mcpserver import Resolve
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import db as db_dependencies
from src.application.access.repositories import AccessGrantRepository
from src.application.articles.repositories import ArticleQueryRepository, ArticleRepository, ArticleRevisionRepository
from src.application.search.indexes import SearchIndexReader
from src.application.search.types import TextEmbedder
from src.application.spaces.repositories import SpaceRepository
from src.infra.database.repositories import (
    SqlAlchemyAccessGrantRepository,
    SqlAlchemyArticleQueryRepository,
    SqlAlchemyArticleRepository,
    SqlAlchemyArticleRevisionRepository,
    SqlAlchemySpaceRepository,
)

from .state import McpContext, McpState

_db_session: ContextVar[AsyncSession] = ContextVar("mcp_db_session")


async def with_db_session(ctx: ServerRequestContext[McpState], call_next: CallNext) -> HandlerResult:
    if ctx.method != "tools/call":
        return await call_next(ctx)

    async with db_dependencies.sessionmaker() as session:
        token = _db_session.set(session)
        try:
            return await call_next(ctx)
        finally:
            _db_session.reset(token)


def _get_db_session() -> AsyncSession:
    return _db_session.get()


DBSession = Annotated[AsyncSession, Resolve(_get_db_session)]


def get_grant_repository(session: DBSession) -> AccessGrantRepository:
    return SqlAlchemyAccessGrantRepository(session)


def get_article_repository(session: DBSession) -> ArticleRepository:
    return SqlAlchemyArticleRepository(session)


def get_revision_repository(session: DBSession) -> ArticleRevisionRepository:
    return SqlAlchemyArticleRevisionRepository(session)


def get_article_query_repository(session: DBSession) -> ArticleQueryRepository:
    return SqlAlchemyArticleQueryRepository(session)


def get_space_repository(session: DBSession) -> SpaceRepository:
    return SqlAlchemySpaceRepository(session)


def get_search_index(ctx: McpContext) -> SearchIndexReader:
    return ctx.request_context.lifespan_context.search_index


def get_embedder(ctx: McpContext) -> TextEmbedder:
    return ctx.request_context.lifespan_context.embedder


GrantRepositoryDep = Annotated[AccessGrantRepository, Resolve(get_grant_repository)]
ArticleRepositoryDep = Annotated[ArticleRepository, Resolve(get_article_repository)]
RevisionRepositoryDep = Annotated[ArticleRevisionRepository, Resolve(get_revision_repository)]
ArticleQueryRepositoryDep = Annotated[ArticleQueryRepository, Resolve(get_article_query_repository)]
SpaceRepositoryDep = Annotated[SpaceRepository, Resolve(get_space_repository)]
SearchIndexDep = Annotated[SearchIndexReader, Resolve(get_search_index)]
TextEmbedderDep = Annotated[TextEmbedder, Resolve(get_embedder)]
