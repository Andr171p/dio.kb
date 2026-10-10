from uuid import UUID

from ddf.application.exceptions import NotFoundError

from src.application.access import (
    AccessGrantRepository,
    Permission,
    Resource,
    ensure_access,
    resolve_permissions,
)
from src.application.auth.dtos import AuthUser
from src.domain.collections.models import Collection

from .repositories import CollectionPlacementRepository, CollectionRepository


async def get_accessible_collection(
    collection_id: UUID,
    auth: AuthUser,
    required: Permission,
    *,
    collection_repository: CollectionRepository,
    placement_repository: CollectionPlacementRepository,
    grant_repository: AccessGrantRepository,
) -> Collection:
    """
    Загружает активную коллекцию и проверяет права с учётом Space и цепочки родителей.

    Права на коллекцию регулируют навигацию, но не дают доступа к содержимому статей.
    """

    collection = await collection_repository.read(collection_id)

    if collection is None or collection.is_deleted or collection.organization_id != auth.user.organization_id:
        raise NotFoundError(f"Collection with ID {collection_id} not found.")

    resources = await collection_resources(collection, placement_repository=placement_repository)
    await ensure_access(auth, resources, required, grant_repository=grant_repository)
    return collection


async def collection_resources(
    collection: Collection, *, placement_repository: CollectionPlacementRepository
) -> tuple[Resource, ...]:
    """Цепочка ресурсов коллекции: Space, родители и сама коллекция."""

    ancestor_ids = await placement_repository.find_collection_ancestor_ids(collection.id)
    return (
        Resource(type="space", id=collection.space_id),
        *(Resource(type="collection", id=ancestor_id) for ancestor_id in ancestor_ids),
        Resource(type="collection", id=collection.id),
    )


async def resolve_collection_permissions(
    collection: Collection,
    auth: AuthUser,
    *,
    placement_repository: CollectionPlacementRepository,
    grant_repository: AccessGrantRepository,
) -> Permission:
    resources = await collection_resources(collection, placement_repository=placement_repository)
    return await resolve_permissions(auth, resources, grant_repository=grant_repository)


__all__ = ["collection_resources", "get_accessible_collection", "resolve_collection_permissions"]
