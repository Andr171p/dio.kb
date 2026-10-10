import hashlib
import logging
from collections.abc import Sequence
from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID

from ddf.application.uow import UnitOfWork

from src.application.articles.repositories import ArticleRepository, ArticleRevisionRepository
from src.domain.articles.models import Article, ArticleRevision

from .markdown import MarkdownChunk, chunk_id, split_markdown
from .models import ArticleIndexState, ImageText, SearchChunk
from .protocols import ImageTextExtractor, MediaStorage, TextEmbedder
from .repositories import ArticleIndexStateRepository, ImageTextRepository, SearchChunkRepository

logger = logging.getLogger(__name__)


async def _extract_images(
    media_ids: Sequence[UUID],
    *,
    media_storage: MediaStorage,
    image_extractor: ImageTextExtractor,
    image_text_repository: ImageTextRepository,
) -> tuple[dict[UUID, ImageText], tuple[UUID, ...]]:
    """Распознаёт изображения с кешем; сбой одного изображения не прерывает индексацию статьи."""

    image_texts = await image_text_repository.find(media_ids, image_extractor.version)
    failed: list[UUID] = []

    for media_id in media_ids:
        if media_id in image_texts:
            continue

        try:
            media = await media_storage.download(media_id)
            if not image_extractor.supports(media.content_type):
                continue

            image_text = await image_extractor.extract(media)
        except Exception:
            logger.exception("Image text extraction failed", extra={"media_id": str(media_id)})
            failed.append(media_id)
            continue

        await image_text_repository.save(media_id, image_extractor.version, image_text)
        image_texts[media_id] = image_text

    return image_texts, tuple(failed)


def _build_search_text(
    title: str,
    heading_path: tuple[str, ...],
    text: str,
    image_texts: Sequence[ImageText],
) -> str:
    parts = [" › ".join((title, *heading_path)), text]

    for image_text in image_texts:
        image_parts = [f"Изображение: {image_text.description}"] if image_text.description else []
        if image_text.text:
            image_parts.append(f"Текст на изображении: {image_text.text}")
        parts.append("\n".join(image_parts))

    return "\n\n".join(part for part in parts if part)


def _build_chunks(
    article: Article,
    revision: ArticleRevision,
    markdown_chunks: Sequence[MarkdownChunk],
    image_texts: dict[UUID, ImageText],
) -> list[SearchChunk]:
    sections: list[tuple[tuple[str, ...], str | None, str, tuple[UUID, ...]]] = []

    if revision.summary:
        sections.append(((), None, revision.summary, ()))

    sections.extend(
        (chunk.heading_path, chunk.anchor, chunk.text, chunk.media_ids) for chunk in markdown_chunks
    )

    chunks: list[SearchChunk] = []
    for position, (heading_path, anchor, text, media_ids) in enumerate(sections):
        search_text = _build_search_text(
            revision.title,
            heading_path,
            text,
            [image_texts[media_id] for media_id in media_ids if media_id in image_texts],
        )
        chunks.append(
            SearchChunk(
                id=chunk_id(article.id, revision.id, position),
                organization_id=article.organization_id,
                space_id=article.space_id,
                article_id=article.id,
                revision_id=revision.id,
                position=position,
                heading_path=heading_path,
                anchor=anchor,
                text=text,
                search_text=search_text,
                content_hash=hashlib.sha256(search_text.encode()).hexdigest(),
                media_ids=media_ids,
            )
        )

    return chunks


async def _embed_chunks(
    article_id: UUID,
    chunks: list[SearchChunk],
    *,
    embedder: TextEmbedder,
    chunk_repository: SearchChunkRepository,
) -> list[SearchChunk]:
    """Эмбеддинги только для изменившихся фрагментов, остальные берутся из индекса по ``content_hash``."""

    vectors = await chunk_repository.find_article_vectors(article_id)
    missing = list(
        {
            chunk.content_hash: chunk.search_text for chunk in chunks if chunk.content_hash not in vectors
        }.items(),
    )

    if missing:
        embeddings = await embedder.embed_documents([search_text for _, search_text in missing])
        vectors.update(
            (content_hash, vector) for (content_hash, _), vector in zip(missing, embeddings, strict=True)
        )

    logger.info("Embedded %d of %d chunks", len(missing), len(chunks), extra={"article_id": str(article_id)})
    return [replace(chunk, dense_vector=vectors[chunk.content_hash]) for chunk in chunks]


async def sync_article_index(
    article_id: UUID,
    *,
    article_repository: ArticleRepository,
    revision_repository: ArticleRevisionRepository,
    chunk_repository: SearchChunkRepository,
    index_state_repository: ArticleIndexStateRepository,
    image_text_repository: ImageTextRepository,
    media_storage: MediaStorage,
    image_extractor: ImageTextExtractor,
    embedder: TextEmbedder,
    uow: UnitOfWork,
) -> None:
    """
    Приводит индекс статьи к её актуальному состоянию в PostgreSQL (идемпотентно).

    Не доверяет содержимому события: читает текущую опубликованную редакцию, готовит фрагменты
    вне транзакции, затем под блокировкой статьи перепроверяет, что публикация не изменилась.
    Если изменилась — выходит: новое событие уже поставило следующую синхронизацию.
    """

    article = await article_repository.read(article_id)
    revision = None

    if article is not None and article.is_published and article.published_revision_id is not None:
        revision = await revision_repository.read(article.published_revision_id)

    chunks: list[SearchChunk] = []
    failed_media_ids: tuple[UUID, ...] = ()

    if article is not None and revision is not None:
        markdown_chunks = split_markdown(revision.content)
        media_ids = list(dict.fromkeys(media_id for chunk in markdown_chunks for media_id in chunk.media_ids))
        image_texts, failed_media_ids = await _extract_images(
            media_ids,
            media_storage=media_storage,
            image_extractor=image_extractor,
            image_text_repository=image_text_repository,
        )
        await uow.commit()

        chunks = await _embed_chunks(
            article.id,
            _build_chunks(article, revision, markdown_chunks, image_texts),
            embedder=embedder,
            chunk_repository=chunk_repository,
        )
    else:
        await uow.commit()

    expected_revision_id = revision.id if revision is not None else None

    await index_state_repository.lock(article_id)
    actual = await article_repository.read(article_id)
    actual_revision_id = actual.published_revision_id if actual is not None and actual.is_published else None

    if actual_revision_id != expected_revision_id:
        await uow.rollback()
        logger.info(
            "Article changed during indexing, skipping stale job", extra={"article_id": str(article_id)}
        )
        return

    if expected_revision_id is None:
        await chunk_repository.delete_article_chunks(article_id)
    else:
        await chunk_repository.replace_article_chunks(article_id, expected_revision_id, chunks)

    await index_state_repository.save(
        ArticleIndexState(
            article_id=article_id,
            revision_id=expected_revision_id,
            index_name=chunk_repository.index_name,
            chunk_count=len(chunks),
            indexed_at=datetime.now(UTC),
            failed_media_ids=failed_media_ids,
        )
    )
    await uow.commit()

    logger.info(
        "Article index synced",
        extra={
            "article_id": str(article_id),
            "revision_id": str(expected_revision_id),
            "chunks": len(chunks),
        },
    )
