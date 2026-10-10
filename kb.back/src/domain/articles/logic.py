import uuid
from uuid import UUID

from ddf.domain.exceptions import InvariantViolationError

from .models import Article, ArticleRevision


def create_article_with_first_revision(
    *,
    organization_id: UUID,
    space_id: UUID,
    author_id: UUID,
    slug: str,
    title: str,
    content: str,
    summary: str | None = None,
) -> tuple[Article, ArticleRevision]:
    """Создаёт статью с первой редакцией."""

    article_id = uuid.uuid7()

    revision = ArticleRevision(
        article_id=article_id,
        number=1,
        title=title,
        summary=summary,
        content=content,
        author_id=author_id,
    )

    article = Article(
        id=article_id,
        organization_id=organization_id,
        space_id=space_id,
        slug=slug,
        current_revision_id=revision.id,
        revision_number=1,
        author_id=author_id,
    )

    return article, revision


def revise_article(
    article: Article,
    *,
    based_on_revision_id: UUID,
    author_id: UUID,
    title: str,
    content: str,
    summary: str | None = None,
    change_note: str | None = None,
) -> ArticleRevision:
    """Создаёт следующую редакцию поверх ``based_on_revision_id`` (optimistic concurrency)."""

    previous_revision_id = article.current_revision_id
    revision_id = uuid.uuid7()
    number = article.revise(revision_id, based_on_revision_id=based_on_revision_id)

    return ArticleRevision(
        id=revision_id,
        article_id=article.id,
        number=number,
        previous_revision_id=previous_revision_id,
        title=title,
        summary=summary,
        content=content,
        author_id=author_id,
        change_note=change_note,
    )


def restore_article_revision(
    article: Article,
    source: ArticleRevision,
    *,
    based_on_revision_id: UUID,
    author_id: UUID,
    change_note: str | None = None,
) -> ArticleRevision:
    """Создаёт новую редакцию с содержимым исторической ``source``."""

    if article.id != source.article_id:
        raise InvariantViolationError(f"Revision {source.id!r} does not belong to article {article.id!r}.")

    revision = revise_article(
        article,
        based_on_revision_id=based_on_revision_id,
        author_id=author_id,
        title=source.title,
        content=source.content,
        summary=source.summary,
        change_note=change_note,
    )
    revision.restored_from_revision_id = source.id
    return revision


__all__ = ["create_article_with_first_revision", "restore_article_revision", "revise_article"]
