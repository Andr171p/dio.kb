from contextlib import asynccontextmanager
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.application.indexing.commands import ReconcileIndex
from src.application.indexing.indexing import index_article
from src.application.indexing.reconciliation import reconcile_index
from src.application.indexing.types import IndexOutcome
from src.domain.articles.logic import create_article_with_first_revision


@asynccontextmanager
async def lock(*args):
    yield


@pytest.mark.asyncio
async def test_publication_changed_during_preparation_never_writes_index():
    article, revision = create_article_with_first_revision(
        organization_id=uuid4(), space_id=uuid4(), author_id=uuid4(), slug="test", title="test", content="content"
    )
    article.publish(revision.id)
    load = AsyncMock(side_effect=[(article, revision), None])
    writer = type("Index", (), {"generation": "g1", "sync_revision": AsyncMock(), "delete_article": AsyncMock()})()
    checkpoints = type("Checkpoints", (), {"get": AsyncMock(return_value=None)})()
    result = await index_article(
        article.organization_id,
        article.id,
        load_publication=load,
        prepare_chunks=AsyncMock(return_value=[]),
        lock_article=lock,
        index_writer=writer,
        checkpoint_store=checkpoints,
    )
    assert result == IndexOutcome.SUPERSEDED
    writer.sync_revision.assert_not_awaited()
    writer.delete_article.assert_not_awaited()


@pytest.mark.asyncio
async def test_rebuild_enqueues_forced_indexing():
    org, article = uuid4(), uuid4()
    candidates = AsyncMock(return_value=(article,))
    enqueue = AsyncMock(return_value=uuid4())
    result = await reconcile_index(
        ReconcileIndex(organization_id=org, generation="g1", mode="rebuild"),
        find_candidates=candidates,
        enqueue=enqueue,
    )
    assert result == 1
    assert enqueue.await_args.args[0].force is True
