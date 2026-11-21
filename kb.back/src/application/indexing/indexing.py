import logging
from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID

from src.domain.articles.models import PublishedArticle

from .checkpoint import IndexCheckpoint, IndexCheckpointStore
from .models import IndexedChunk
from .search_index_writer import SearchIndexWriter
from .types import IndexOutcome, LoadPublication, LockArticleIndex, PrepareArticleChunks

logger = logging.getLogger(__name__)


def _publication_key(published: PublishedArticle | None) -> tuple[UUID, UUID, UUID, UUID] | None:
    """Идентичность состояния публикации, влияющего на индекс."""

    if published is None:
        return None

    article, revision = published

    return article.organization_id, article.id, article.space_id, revision.id


def _is_indexed(checkpoint: IndexCheckpoint | None, published: PublishedArticle, generation: str) -> bool:
    if checkpoint is None:
        return False

    article, revision = published

    return (
        checkpoint.article_id == article.id
        and checkpoint.revision_id == revision.id
        and checkpoint.space_id == article.space_id
        and checkpoint.generation == generation
    )


async def index_article(
    organization_id: UUID,
    article_id: UUID,
    *,
    load_publication: LoadPublication,
    prepare_chunks: PrepareArticleChunks,
    lock_article: LockArticleIndex,
    index_writer: SearchIndexWriter,
    checkpoint_store: IndexCheckpointStore,
    force: bool = False,
) -> IndexOutcome:
    """
    Синхронизирует поисковую проекцию с актуальной публикацией.

    Выполняет:
     1. Загрузку текущей публикации.
     2. Проверку checkpoint.
     3. Подготовку индексных документов.
     4. Сериализацию финальной записи.
     5. Повторную проверку публикации.
     6. Синхронизацию с векторной БД и подтверждение checkpoint.
    """

    publication = await load_publication(organization_id, article_id)

    if publication is not None and not force:
        checkpoint = await checkpoint_store.get(article_id, index_writer.generation)
        if _is_indexed(checkpoint, publication, index_writer.generation):
            return IndexOutcome.UNCHANGED

    chunks: Sequence[IndexedChunk] = await prepare_chunks(publication) if publication is not None else ()

    async with lock_article(organization_id, article_id):
        actual = await load_publication(organization_id, article_id)

        if _publication_key(publication) != _publication_key(actual):
            logger.info("Article publication changed during indexing", extra={"article_id": str(article_id)})
            return IndexOutcome.SUPERSEDED

        if actual is None:
            await index_writer.delete_article(organization_id=organization_id, article_id=article_id)
            cleared = await checkpoint_store.clear_if_unpublished(organization_id, article_id, index_writer.generation)

            return IndexOutcome.DELETED if cleared else IndexOutcome.SUPERSEDED

        article, revision = actual

        if not force:
            checkpoint = await checkpoint_store.get(article_id, index_writer.generation)

            if _is_indexed(checkpoint, actual, index_writer.generation):
                return IndexOutcome.UNCHANGED

        await index_writer.sync_revision(
            organization_id=organization_id,
            article_id=article_id,
            revision_id=revision.id,
            chunks=chunks,
        )
        confirmed = await checkpoint_store.save_if_current(
            organization_id,
            IndexCheckpoint(
                article_id=article.id,
                revision_id=revision.id,
                space_id=article.space_id,
                generation=index_writer.generation,
                indexed_at=datetime.now(UTC),
            ),
        )
        if not confirmed:
            return IndexOutcome.SUPERSEDED

    logger.info(
        "Article indexed",
        extra={"article_id": str(article_id), "revision_id": str(revision.id), "chunks": len(chunks)},
    )
    return IndexOutcome.INDEXED
