from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.application.articles.projections import PublishedArticle
from src.application.search.dtos import SearchRequest
from src.application.search.models import ArticleMatch, ChunkHit
from src.application.search.usecases import search_articles
from src.domain.access.vo import Resource


@pytest.mark.asyncio
async def test_empty_scope_never_calls_embedder_or_index():
    org = uuid4()
    grants = type("Grants", (), {"find_accessible_resources": AsyncMock(return_value=frozenset())})()
    embed = AsyncMock()
    index = type("Index", (), {"search": AsyncMock()})()
    result = await search_articles(
        org,
        None,
        SearchRequest(query="vpn"),
        grant_repository=grants,
        article_query_repository=None,
        search_index=index,
        embedder=embed,
    )
    assert result.items == []
    embed.assert_not_awaited()
    index.search.assert_not_awaited()


@pytest.mark.asyncio
async def test_unreadable_and_stale_fragments_never_returned():
    org, space, article, other, revision = (uuid4() for _ in range(5))
    grants = type(
        "Grants",
        (),
        {"find_accessible_resources": AsyncMock(return_value=frozenset({Resource(type="space", id=space)}))},
    )()

    def hit(aid, rev):
        return ChunkHit(chunk_id=uuid4(), article_id=aid, revision_id=rev, score=1, markdown="secret", heading_path=())

    candidates = [ArticleMatch(article, 1, (hit(article, uuid4()),)), ArticleMatch(other, 1, (hit(other, revision),))]
    index = type("Index", (), {"search": AsyncMock(return_value=candidates)})()
    queries = type(
        "Queries",
        (),
        {
            "find_readable_published": AsyncMock(
                return_value=(PublishedArticle(article, space, "a", "A", revision, datetime.now(UTC)),)
            )
        },
    )()
    result = await search_articles(
        org,
        None,
        SearchRequest(query="vpn"),
        grant_repository=grants,
        article_query_repository=queries,
        search_index=index,
        embedder=AsyncMock(return_value=[0.1]),
    )
    assert result.items == []
