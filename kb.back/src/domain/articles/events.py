from typing import ClassVar

from dataclasses import dataclass
from uuid import UUID

from ddf.domain.events import Event


@dataclass(kw_only=True, frozen=True)
class ArticlePublished(Event):
    event_type: ClassVar[str] = "article.published"

    organization_id: UUID
    article_id: UUID
    revision_id: UUID


@dataclass(kw_only=True, frozen=True)
class ArticleUnpublished(Event):
    event_type: ClassVar[str] = "article.unpublished"

    organization_id: UUID
    article_id: UUID


@dataclass(kw_only=True, frozen=True)
class ArticleArchived(Event):
    event_type: ClassVar[str] = "article.archived"

    organization_id: UUID
    article_id: UUID
