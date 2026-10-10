from dataclasses import dataclass
from uuid import UUID

from ddf.domain.models import AggregateRoot, Entity

from .vo import CollectionTarget


@dataclass(kw_only=True)
class Collection(AggregateRoot):
    """Навигационная группа статей и вложенных коллекций внутри Space."""

    organization_id: UUID
    space_id: UUID
    name: str
    slug: str
    description: str | None = None


@dataclass(kw_only=True)
class CollectionPlacement(Entity):
    """Размещение статьи или коллекции внутри коллекции с порядком ``rank``."""

    collection_id: UUID
    target: CollectionTarget
    rank: str
