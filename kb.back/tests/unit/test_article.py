import uuid

import pytest
from ddf.domain.exceptions import InvalidStateError

from src.domain.articles import logic
from src.domain.articles.events import ArticleArchived, ArticlePublished
from src.domain.articles.exceptions import ArticleRevisionConflictError
from src.domain.articles.types import ArticleStatus


def _article():
    return logic.create_article_with_first_revision(
        organization_id=uuid.uuid4(),
        space_id=uuid.uuid4(),
        author_id=uuid.uuid4(),
        slug="a",
        title="A",
        content="x",
    )


def test_revision_based_on_stale_version_conflicts() -> None:
    article, first = _article()
    logic.revise_article(
        article, based_on_revision_id=first.id, author_id=uuid.uuid4(), title="B", content="y"
    )

    with pytest.raises(ArticleRevisionConflictError):
        logic.revise_article(
            article, based_on_revision_id=first.id, author_id=uuid.uuid4(), title="C", content="z"
        )


def test_only_current_revision_can_be_published() -> None:
    article, first = _article()
    second = logic.revise_article(
        article, based_on_revision_id=first.id, author_id=uuid.uuid4(), title="B", content="y"
    )

    with pytest.raises(ArticleRevisionConflictError):
        article.publish(first.id)

    article.publish(second.id)
    assert article.status is ArticleStatus.PUBLISHED
    assert [type(event) for event in article.collect_events()] == [ArticlePublished]


def test_archive_hides_publication_and_restore_returns_draft() -> None:
    article, first = _article()
    article.publish(first.id)
    article.archive()

    assert article.status is ArticleStatus.ARCHIVED
    assert not article.is_published
    assert isinstance(list(article.collect_events())[-1], ArticleArchived)
    with pytest.raises(InvalidStateError):
        article.publish(first.id)

    article.restore()
    assert article.status is ArticleStatus.DRAFT
