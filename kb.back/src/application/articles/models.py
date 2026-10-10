from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class PublishedArticle:
    """Актуальное опубликованное состояние статьи по данным PostgreSQL."""

    id: UUID
    space_id: UUID
    slug: str
    title: str
    published_revision_id: UUID
    published_at: datetime
