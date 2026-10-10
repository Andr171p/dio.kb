from uuid import UUID

from ddf.application.exceptions import NotFoundError

from src.application.access import AccessGrantRepository, Permission, Resource, ensure_access
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

    ancestor_ids = await placement_repository.find_collection_ancestor_ids(collection.id)
    resources = (
        Resource(type="space", id=collection.space_id),
        *(Resource(type="collection", id=ancestor_id) for ancestor_id in ancestor_ids),
        Resource(type="collection", id=collection.id),
    )
    await ensure_access(auth, resources, required, grant_repository=grant_repository)
    return collection


__all__ = ["get_accessible_collection"]
