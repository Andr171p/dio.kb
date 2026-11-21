from typing import Annotated

from contextlib import asynccontextmanager
from contextvars import ContextVar

from mcp.server import ServerRequestContext
from mcp.server.context import CallNext, HandlerResult
from mcp.server.mcpserver import Resolve
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies.access import get_grant_repository
from src.api.dependencies.articles import get_article_query_repository, get_article_repository, get_revision_repository
from src.api.dependencies.db import get_db
from src.api.dependencies.spaces import get_space_repository
from src.application.access.repositories import AccessGrantRepository
from src.application.articles.repositories import ArticleQueryRepository, ArticleRepository, ArticleRevisionRepository
from src.application.search.indexes import SearchIndexReader
from src.application.search.types import TextEmbedder
from src.application.spaces.repositories import SpaceRepository

from .state import McpContext, McpState

_db_session: ContextVar[AsyncSession] = ContextVar("mcp_db_session")


async def with_db_session(ctx: ServerRequestContext[McpState], call_next: CallNext) -> HandlerResult:
    if ctx.method != "tools/call":
        return await call_next(ctx)

    async with asynccontextmanager(get_db)() as session:
        token = _db_session.set(session)
        try:
            return await call_next(ctx)
        finally:
            _db_session.reset(token)


def _get_db_session() -> AsyncSession:
    return _db_session.get()


DBSession = Annotated[AsyncSession, Resolve(_get_db_session)]


def _get_grant_repository(session: DBSession) -> AccessGrantRepository:
    return get_grant_repository(session)


def _get_article_repository(session: DBSession) -> ArticleRepository:
    return get_article_repository(session)


def _get_revision_repository(session: DBSession) -> ArticleRevisionRepository:
    return get_revision_repository(session)


def _get_article_query_repository(session: DBSession) -> ArticleQueryRepository:
    return get_article_query_repository(session)


def _get_space_repository(session: DBSession) -> SpaceRepository:
    return get_space_repository(session)


def _get_search_index(ctx: McpContext) -> SearchIndexReader:
    return ctx.request_context.lifespan_context.search_index


def _get_embedder(ctx: McpContext) -> TextEmbedder:
    return ctx.request_context.lifespan_context.embedder


GrantRepositoryDep = Annotated[AccessGrantRepository, Resolve(_get_grant_repository)]
ArticleRepositoryDep = Annotated[ArticleRepository, Resolve(_get_article_repository)]
RevisionRepositoryDep = Annotated[ArticleRevisionRepository, Resolve(_get_revision_repository)]
ArticleQueryRepositoryDep = Annotated[ArticleQueryRepository, Resolve(_get_article_query_repository)]
SpaceRepositoryDep = Annotated[SpaceRepository, Resolve(_get_space_repository)]
SearchIndexDep = Annotated[SearchIndexReader, Resolve(_get_search_index)]
TextEmbedderDep = Annotated[TextEmbedder, Resolve(_get_embedder)]
