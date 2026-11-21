import os
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import update
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.application.indexing.checkpoint import IndexCheckpoint
from src.application.indexing.image_analysis import ImageAnalysis
from src.application.indexing.reconciliation import ReconciliationQuery
from src.domain.access.types import Permission
from src.domain.access.vo import Subject
from src.domain.articles.logic import create_article_with_first_revision
from src.infra.database.models import AccessGrantOrm, ArticleOrm, SpaceOrm
from src.infra.database.repositories.article import ArticleMapper
from src.infra.database.repositories.article_query import SqlAlchemyArticleQueryRepository
from src.infra.database.indexing.embedding_cache import SqlAlchemyEmbeddingCache
from src.infra.database.indexing.image_analysis_cache import SqlAlchemyImageAnalysisCache
from src.infra.database.indexing.checkpoints import SqlAlchemyIndexCheckpointStore
from src.infra.database.indexing.locks import lock_article
from src.infra.database.repositories.publication import load_publication
from src.infra.database.repositories.reconciliation import find_candidates
from src.infra.database.repositories.revision import ArticleRevisionMapper


@pytest.mark.asyncio
async def test_postgres_indexing_and_readable_publications():
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL is not configured")
    engine = create_async_engine(url)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    org, space, author = uuid4(), uuid4(), uuid4()
    article, revision = create_article_with_first_revision(
        organization_id=org, space_id=space, author_id=author, slug=str(uuid4()), title="VPN", content="secret"
    )
    article.publish(revision.id)
    async with sessions() as session, session.begin():
        session.add(SpaceOrm(id=space, organization_id=org, key=str(space)[:32], name="test", created_by=author))
        await session.flush()
        session.add(ArticleMapper.to_model(article))
        session.add(ArticleRevisionMapper.to_model(revision))
        session.add(
            AccessGrantOrm(
                organization_id=org,
                granted_by=author,
                resource_type="space",
                resource_id=space,
                subject_type="role",
                subject_id="reader",
                permissions=int(Permission.READ),
            )
        )
    repository = SqlAlchemyIndexCheckpointStore(sessions)
    checkpoints = IndexCheckpoint(article.id, revision.id, space, "g1", datetime.now(UTC))
    async with lock_article(org, article.id, sessionmaker=sessions):
        assert await load_publication(org, article.id, sessionmaker=sessions) is not None
    assert (await load_publication(org, article.id, sessionmaker=sessions))[1].id == revision.id
    assert await repository.save_if_current(org, checkpoints)
    assert await repository.get(article.id, "g1") == checkpoints
    assert await find_candidates(ReconciliationQuery(org, "g1", "stale"), sessionmaker=sessions) == ()
    async with sessions() as session:
        queries = SqlAlchemyArticleQueryRepository(session)
        assert (
            len(await queries.find_readable_published(org, [article.id], subjects={Subject(type="role", id="reader")}))
            == 1
        )
        assert not await queries.find_readable_published(org, [article.id], subjects={Subject(type="role", id="other")})
    images = SqlAlchemyImageAnalysisCache(sessions)
    media = uuid4()
    await images.put(media, "v1", ImageAnalysis(text="abc", description="image"))
    assert (await images.get_many([media], "v1"))[media].text == "abc"
    embeddings = SqlAlchemyEmbeddingCache(sessions)
    await embeddings.put_many({"hash": (0.5, 1.0)}, "v1")
    assert (await embeddings.get_many(["hash"], "v1"))["hash"] == (0.5, 1.0)
    async with sessions() as session, session.begin():
        await session.execute(update(ArticleOrm).where(ArticleOrm.id == article.id).values(published_revision_id=None))
    assert not await repository.save_if_current(org, checkpoints)
    assert await find_candidates(ReconciliationQuery(org, "g1", "stale"), sessionmaker=sessions) == (article.id,)
    assert not await repository.clear_if_unpublished(uuid4(), article.id, "g1")
    assert await repository.clear_if_unpublished(org, article.id, "g1")
    await engine.dispose()
