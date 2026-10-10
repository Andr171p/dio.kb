from datetime import UTC, datetime

from ddf.domain.utils import apply_changes

from src.domain.collections.models import Collection

from .dtos import CollectionResponse, CreateCollectionDTO, UpdateCollectionDTO


async def create_collection_handler(dto: CreateCollectionDTO, _: object = None) -> Collection:
    return Collection(space_id=dto.space_id, name=dto.name, slug=dto.slug, description=dto.description)


async def update_collection_handler(
    collection: Collection,
    dto: UpdateCollectionDTO,
    _: object = None,
) -> Collection:
    apply_changes(collection, **dto.model_dump(exclude_unset=True))
    return collection


async def delete_collection_handler(collection: Collection, _: object = None) -> Collection:
    apply_changes(collection, deleted_at=datetime.now(UTC))
    return collection


def to_collection_response(collection: Collection) -> CollectionResponse:
    return CollectionResponse.model_validate(collection)
