from collections.abc import Awaitable, Callable, Sequence
from dataclasses import replace
from uuid import UUID

from src.domain.articles.models import PublishedArticle

from .chunks import build_indexed_chunks, collect_media_ids
from .image_analysis import ImageAnalysis
from .markdown import MarkdownChunk, split_markdown
from .models import IndexedChunk

type AnalyzeImages = Callable[
    [Sequence[UUID]],
    Awaitable[tuple[dict[UUID, ImageAnalysis], tuple[UUID, ...]]],
]

type EmbedChunks = Callable[[Sequence[IndexedChunk]], Awaitable[list[IndexedChunk]],]


class IncompleteImageAnalysisError(RuntimeError):
    """Не удалось полностью обработать медиа статьи."""

    def __init__(self, media_ids: tuple[UUID, ...]) -> None:
        self.media_ids = media_ids
        super().__init__(f"Failed to analyze {len(media_ids)} media objects.")


async def prepare_article_chunks(
    published: PublishedArticle,
    *,
    analyze: AnalyzeImages,
    embed: EmbedChunks,
    target_chars: int,
) -> list[IndexedChunk]:
    """Подготавливает индексные документы опубликованной редакции."""

    article, revision = published
    if revision.article_id != article.id:
        raise ValueError("Revision does not belong to article.")

    sections: list[MarkdownChunk] = []

    if revision.summary:
        sections.extend(
            replace(chunk, anchor=None)
            for chunk in split_markdown(revision.summary, target_chars=target_chars)
        )

    sections.extend(split_markdown(revision.content, target_chars=target_chars))

    if not sections:
        sections.append(MarkdownChunk(heading_path=(), anchor=None, markdown=revision.title))

    analyses, failed = await analyze(collect_media_ids(sections))

    if failed:
        raise IncompleteImageAnalysisError(failed)

    chunks = build_indexed_chunks(article, revision, sections, analyses)

    return await embed(chunks)
