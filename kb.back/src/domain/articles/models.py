from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from ddf.domain.exceptions import InvalidStateError
from ddf.domain.models import AggregateRoot, Entity

from .events import ArticleArchived, ArticlePublished, ArticleUnpublished
from .exceptions import ArticleRevisionConflictError
from .types import ArticleStatus


@dataclass(kw_only=True)
class Article(AggregateRoot):
    """Статья: жизненный цикл и указатели на редакторскую и опубликованную редакции."""

    organization_id: UUID
    space_id: UUID

    slug: str

    current_revision_id: UUID
    published_revision_id: UUID | None = None
    revision_number: int

    author_id: UUID
    published_at: datetime | None = None

    @property
    def status(self) -> ArticleStatus:
        if self.is_deleted:
            return ArticleStatus.ARCHIVED

        if self.published_revision_id is None:
            return ArticleStatus.DRAFT

        return ArticleStatus.PUBLISHED

    @property
    def is_published(self) -> bool:
        return not self.is_deleted and self.published_revision_id is not None

    @property
    def has_unpublished_changes(self) -> bool:
        return self.is_published and self.published_revision_id != self.current_revision_id

    def _ensure_not_archived(self) -> None:
        if self.is_deleted:
            raise InvalidStateError("Archived article cannot be modified.")

    def revise(self, revision_id: UUID, *, based_on_revision_id: UUID) -> int:
        """Переключает редакторскую версию на новую редакцию и возвращает её номер."""

        self._ensure_not_archived()

        if based_on_revision_id != self.current_revision_id:
            raise ArticleRevisionConflictError("Article has been modified since this revision was opened.")

        self.revision_number += 1
        self.current_revision_id = revision_id
        self.updated_at = datetime.now(UTC)

        return self.revision_number

    def publish(self, revision_id: UUID) -> None:
        """Публикует текущую редакцию; ``revision_id`` защищает от публикации незнакомых изменений."""

        self._ensure_not_archived()

        if revision_id != self.current_revision_id:
            raise ArticleRevisionConflictError("Only the current revision can be published.")

        self.published_revision_id = self.current_revision_id
        self.published_at = self.updated_at = datetime.now(UTC)

        self.register_event(
            ArticlePublished(
                organization_id=self.organization_id,
                article_id=self.id,
                revision_id=self.published_revision_id,
            )
        )

    def unpublish(self) -> None:
        self._ensure_not_archived()

        if self.published_revision_id is None:
            raise InvalidStateError("Article is not published.")

        self.published_revision_id = None
        self.published_at = None
        self.updated_at = datetime.now(UTC)

        self.register_event(ArticleUnpublished(organization_id=self.organization_id, article_id=self.id))

    def archive(self) -> None:
        """Архивирует статью; публикация снимается, восстановленная статья вернётся черновиком."""

        self._ensure_not_archived()

        self.published_revision_id = None
        self.published_at = None
        self.deleted_at = self.updated_at = datetime.now(UTC)

        self.register_event(ArticleArchived(organization_id=self.organization_id, article_id=self.id))

    def restore(self) -> None:
        if not self.is_deleted:
            raise InvalidStateError("Article is not archived.")

        self.deleted_at = None
        self.updated_at = datetime.now(UTC)


@dataclass(kw_only=True)
class ArticleRevision(Entity):
    """Неизменяемая после создания редакция статьи в Markdown."""

    article_id: UUID
    number: int

    previous_revision_id: UUID | None = None
    restored_from_revision_id: UUID | None = None

    title: str
    summary: str | None = None
    content: str

    author_id: UUID
    change_note: str | None = None
