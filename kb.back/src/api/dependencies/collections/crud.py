from typing import Annotated

from ddf.application.crud import Crud
from fastapi import Depends

from src.application.collections.crud import (
    create_collection_handler,
    delete_collection_handler,
    to_collection_response,
    update_collection_handler,
)
from src.application.collections.dtos import CollectionResponse, CreateCollectionDTO, UpdateCollectionDTO
from src.application.collections.repositories import CollectionRepository
from src.domain.collections.models import Collection

type CollectionCrud = Crud[
    Collection,
    CollectionResponse,
    CreateCollectionDTO,
    UpdateCollectionDTO,
    None,
    None,
    None,
    None,
]


async def get_collection_repository(db: ...) -> CollectionRepository:
    return ...


CollectionRepositoryDep = Annotated[CollectionRepository, Depends(get_collection_repository)]


async def get_collection_crud(repository: CollectionRepositoryDep, dispatch: ...) -> CollectionCrud:
    return Crud(
        repository=repository,
        dispatcher=dispatch,
        to_response=to_collection_response,
        create_handler=create_collection_handler,
        update_handler=update_collection_handler,
        delete_handler=delete_collection_handler,
    )


CollectionCrudDep = Annotated[CollectionCrud, Depends(get_collection_crud)]
