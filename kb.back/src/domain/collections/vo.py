from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class TargetType(StrEnum):
    ARTICLE = "article"
    COLLECTION = "collection"


@dataclass(frozen=True, slots=True)
class CollectionTarget:
    """Элемент, размещаемый в коллекции."""

    type: TargetType
    id: UUID
