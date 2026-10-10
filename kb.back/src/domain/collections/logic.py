from collections.abc import Collection
from uuid import UUID

from ddf.domain.exceptions import InvalidStateError

from src.domain.articles.models import Article

from .exceptions import CollectionCycleError, CollectionSelfPlacementError, CrossSpacePlacementError
from .models import Collection as KbCollection


def ensure_valid_article_placement(*, collection: KbCollection, article: Article) -> None:
    """Проверяет допустимость размещения статьи в коллекции."""

    if article.space_id != collection.space_id:
        raise CrossSpacePlacementError("Article and collection must belong to the same space.")

    if article.is_deleted:
        raise InvalidStateError("Archived article cannot be placed in a collection.")


def ensure_valid_collection_parent(
    *,
    parent: KbCollection,
    child: KbCollection,
    current_parent_id: UUID | None,
    parent_ancestor_ids: Collection[UUID],
) -> None:
    """Проверяет, что ``child`` можно вложить в ``parent``: один родитель, один Space, без циклов."""

    if parent.id == child.id:
        raise CollectionSelfPlacementError(f"Collection {child.id!r} cannot contain itself.")

    if parent.space_id != child.space_id:
        raise CrossSpacePlacementError("Collection cannot be placed into another space.")

    if current_parent_id is not None:
        raise InvalidStateError("Collection already has a parent.")

    if child.id in parent_ancestor_ids:
        raise CollectionCycleError("Collection placement would create a cycle.")
