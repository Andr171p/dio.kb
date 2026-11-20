import hashlib
from collections.abc import Mapping, Sequence
from uuid import UUID

from src.domain.articles.models import Article, ArticleRevision

from .image_analysis import ImageAnalysis
from .markdown import MarkdownChunk, chunk_id
from .models import IndexedChunk


def collect_media_ids(sections: Sequence[MarkdownChunk]) -> tuple[UUID, ...]:
    """Уникальные медиа в порядке появления в документе."""
    return tuple(dict.fromkeys(media_id for section in sections for media_id in section.media_ids))


def build_search_text(title: str, chunk: MarkdownChunk, analyses: Mapping[UUID, ImageAnalysis]) -> str:
    """Формирует текст чанка для полнотекстового и семантического поиска."""

    parts = [" › ".join((title, *chunk.heading_path)), chunk.markdown]

    for media_id in chunk.media_ids:
        if (analysis := analyses.get(media_id)) is None:
            continue

        if analysis.description.strip():
            parts.append(f"Изображение: {analysis.description}")

        if analysis.text.strip():
            parts.append(f"Текст на изображении: {analysis.text}")

    return "\n\n".join(part for part in parts if part)


def build_indexed_chunks(
    article: Article,
    revision: ArticleRevision,
    sections: Sequence[MarkdownChunk],
    analyses: Mapping[UUID, ImageAnalysis],
) -> list[IndexedChunk]:
    """Формирует поисковые документы без вычисления embeddings."""

    # Добавить проверку, что revision принадлежит article

    if revision.article_id != article.id:
        raise ValueError("Revision does not belong to article.")

    chunks: list[IndexedChunk] = []

    for position, chunk in enumerate(sections):
        search_text = build_search_text(revision.title, chunk, analyses)

        chunks.append(
            IndexedChunk(
                id=chunk_id(article.id, revision.id, position),
                organization_id=article.organization_id,
                space_id=article.space_id,
                article_id=article.id,
                revision_id=revision.id,
                position=position,
                heading_path=chunk.heading_path,
                anchor=chunk.anchor,
                markdown=chunk.markdown,
                search_text=search_text,
                content_hash=hashlib.sha256(search_text.encode("utf-8")).hexdigest(),
                media_ids=chunk.media_ids,
            )
        )

    return chunks
