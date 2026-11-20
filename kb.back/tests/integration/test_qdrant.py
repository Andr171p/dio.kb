import os
from uuid import uuid4

import pytest
from pydantic import HttpUrl

from src.application.indexing.models import IndexedChunk
from src.application.search.access import SearchScope
from src.application.search.indexes import SearchOptions
from src.domain.access.vo import Resource
from src.infra.qdrant import QdrantConfig, QdrantSearchIndex


@pytest.mark.asyncio
async def test_qdrant_sync_and_scoped_search():
    url = os.environ.get("TEST_QDRANT_URL")
    if not url:
        pytest.skip("TEST_QDRANT_URL is not configured")
    org, space, article, revision, chunk_id = (uuid4() for _ in range(5))
    index = QdrantSearchIndex(QdrantConfig(url=HttpUrl(url), collection=f"test_{uuid4().hex}", generation=1))
    try:
        await index.ensure_collection(2)
        chunk = IndexedChunk(
            id=chunk_id,
            organization_id=org,
            space_id=space,
            article_id=article,
            revision_id=revision,
            position=0,
            heading_path=(),
            anchor=None,
            markdown="VPN setup",
            search_text="VPN setup",
            content_hash="hash",
            embedding=(1.0, 0.0),
        )
        await index.sync_revision(organization_id=org, article_id=article, revision_id=revision, chunks=[chunk])
        scope = SearchScope(organization_id=org, resources=frozenset({Resource(type="space", id=space)}))
        result = await index.search(
            query="VPN",
            query_embedding=[1.0, 0.0],
            scope=scope,
            space_ids=None,
            options=SearchOptions(candidates_limit=5, max_hits_per_article=3),
        )
        assert result[0].article_id == article
        assert result[0].hits[0].markdown == "VPN setup"
        foreign = SearchScope(organization_id=uuid4(), resources=scope.resources)
        assert not await index.search(
            query="VPN",
            query_embedding=[1.0, 0.0],
            scope=foreign,
            space_ids=None,
            options=SearchOptions(candidates_limit=5, max_hits_per_article=3),
        )
        await index.delete_article(organization_id=org, article_id=article)
        assert not await index.search(
            query="VPN",
            query_embedding=[1.0, 0.0],
            scope=scope,
            space_ids=None,
            options=SearchOptions(candidates_limit=5, max_hits_per_article=3),
        )
    finally:
        await index.close()
