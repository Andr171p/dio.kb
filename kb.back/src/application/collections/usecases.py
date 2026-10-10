from collections import defaultdict
from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID

from ddf.application.exceptions import NotFoundError
from ddf.application.uow import UnitOfWork

from src.application.access import AccessGrantRepository, Permission, Resource, resolve_permissions
from src.application.articles.access import get_accessible_article
from src.application.articles.dtos import ArticleSummaryResponse
from src.application.articles.repositories import ArticleQueryRepository, ArticleRepository
from src.application.auth import AuthUser
from src.application.spaces.access import get_accessible_space
from src.application.spaces.repositories import SpaceRepository
from src.domain.collections.exceptions import CollectionNotEmptyError
from src.domain.collections.logic import ensure_valid_article_placement, ensure_valid_collection_parent
from src.domain.collections.models import Collection, CollectionPlacement
from src.domain.collections.ranking import rank_between
from src.domain.collections.vo import CollectionTarget, TargetType

from .access import get_accessible_collection
from .dtos import (
    CollectionPlacementResponse,
    CollectionResponse,
    CreateCollectionDTO,
    CreatePlacementDTO,
    MovePlacementDTO,
    NavigationNode,
    RelativePosition,
    SpaceNavigationResponse,
    UpdateCollectionDTO,
)
from .exceptions import CollectionTargetAlreadyPlacedError
from .repositories import CollectionPlacementRepository, CollectionRepository


def _resolve_rank(placements: Sequence[CollectionPlacement], position: RelativePosition) -> str:
    """Ранг для вставки относительно соседа; ``placements`` отсортированы по ``rank``."""

    anchor_id = position.before_id or position.after_id

    if anchor_id is None:
        return rank_between(placements[-1].rank if placements else None, None)

    index = next((index for index, placement in enumerate(placements) if placement.id == anchor_id), None)
    if index is None:
        raise NotFoundError(f"Placement {anchor_id} not found in collection.")

    if position.before_id is not None:
        before = placements[index - 1].rank if index > 0 else None
        return rank_between(before, placements[index].rank)

    after = placements[index + 1].rank if index + 1 < len(placements) else None
    return rank_between(placements[index].rank, after)


async def _ensure_target_can_be_placed(
    collection: Collection,
    target: CollectionTarget,
    auth: AuthUser,
    *,
    moving_placement_id: UUID | None = None,
    collection_repository: CollectionRepository,
    placement_repository: CollectionPlacementRepository,
    article_repository: ArticleRepository,
    grant_repository: AccessGrantRepository,
) -> None:
    match target.type:
        case TargetType.ARTICLE:
            article = await get_accessible_article(
                target.id,
                auth,
                Permission.READ,
                article_repository=article_repository,
                grant_repository=grant_repository,
            )
            ensure_valid_article_placement(collection=collection, article=article)

        case TargetType.COLLECTION:
            child = await get_accessible_collection(
                target.id,
                auth,
                Permission.WRITE,
                collection_repository=collection_repository,
                placement_repository=placement_repository,
                grant_repository=grant_repository,
            )
            current_parent = await placement_repository.find_collection_parent(child.id)
            if current_parent is not None and current_parent.id == moving_placement_id:
                current_parent = None

            ensure_valid_collection_parent(
                parent=collection,
                child=child,
                current_parent_id=current_parent.collection_id if current_parent is not None else None,
                parent_ancestor_ids=await placement_repository.find_collection_ancestor_ids(collection.id),
            )


async def create_collection(
    space_id: UUID,
    dto: CreateCollectionDTO,
    auth: AuthUser,
    *,
    space_repository: SpaceRepository,
    collection_repository: CollectionRepository,
    placement_repository: CollectionPlacementRepository,
    article_repository: ArticleRepository,
    grant_repository: AccessGrantRepository,
    uow: UnitOfWork,
) -> CollectionResponse:
    """Создаёт коллекцию (WRITE на Space), при ``parent_id`` — сразу в конце родителя."""

    space = await get_accessible_space(
        space_id,
        auth,
        Permission.WRITE,
        space_repository=space_repository,
        grant_repository=grant_repository,
    )
    collection = Collection(
        organization_id=space.organization_id,
        space_id=space.id,
        name=dto.name,
        slug=dto.slug,
        description=dto.description,
    )
    await collection_repository.create(collection)

    if dto.parent_id is not None:
        await placement_repository.lock_space_tree(space.id)
        parent = await get_accessible_collection(
            dto.parent_id,
            auth,
            Permission.WRITE,
            collection_repository=collection_repository,
            placement_repository=placement_repository,
            grant_repository=grant_repository,
        )
        target = CollectionTarget(type=TargetType.COLLECTION, id=collection.id)
        await _ensure_target_can_be_placed(
            parent,
            target,
            auth,
            collection_repository=collection_repository,
            placement_repository=placement_repository,
            article_repository=article_repository,
            grant_repository=grant_repository,
        )
        siblings = await placement_repository.find_by_collection(parent.id)
        await placement_repository.create(
            CollectionPlacement(
                collection_id=parent.id,
                target=target,
                rank=_resolve_rank(siblings, RelativePosition()),
            )
        )

    await uow.commit()
    return CollectionResponse.model_validate(collection)


async def get_collection(
    collection_id: UUID,
    auth: AuthUser,
    *,
    collection_repository: CollectionRepository,
    placement_repository: CollectionPlacementRepository,
    grant_repository: AccessGrantRepository,
) -> CollectionResponse:
    collection = await get_accessible_collection(
        collection_id,
        auth,
        Permission.READ,
        collection_repository=collection_repository,
        placement_repository=placement_repository,
        grant_repository=grant_repository,
    )
    return CollectionResponse.model_validate(collection)


async def update_collection(
    collection_id: UUID,
    dto: UpdateCollectionDTO,
    auth: AuthUser,
    *,
    collection_repository: CollectionRepository,
    placement_repository: CollectionPlacementRepository,
    grant_repository: AccessGrantRepository,
    uow: UnitOfWork,
) -> CollectionResponse:
    collection = await get_accessible_collection(
        collection_id,
        auth,
        Permission.WRITE,
        collection_repository=collection_repository,
        placement_repository=placement_repository,
        grant_repository=grant_repository,
    )

    if dto.name is not None:
        collection.name = dto.name
    if dto.slug is not None:
        collection.slug = dto.slug
    if "description" in dto.model_fields_set:
        collection.description = dto.description or None

    collection.updated_at = datetime.now(UTC)
    await collection_repository.update(collection)
    await uow.commit()

    return CollectionResponse.model_validate(collection)


async def archive_collection(
    collection_id: UUID,
    auth: AuthUser,
    *,
    collection_repository: CollectionRepository,
    placement_repository: CollectionPlacementRepository,
    grant_repository: AccessGrantRepository,
    uow: UnitOfWork,
) -> None:
    """Архивирует пустую коллекцию и убирает её из родителя; непустую — запрещено (409)."""

    collection = await get_accessible_collection(
        collection_id,
        auth,
        Permission.ARCHIVE,
        collection_repository=collection_repository,
        placement_repository=placement_repository,
        grant_repository=grant_repository,
    )
    await placement_repository.lock_space_tree(collection.space_id)

    if await placement_repository.find_by_collection(collection.id):
        raise CollectionNotEmptyError("Collection is not empty.")

    if (parent_placement := await placement_repository.find_collection_parent(collection.id)) is not None:
        await placement_repository.delete(parent_placement.id)

    collection.deleted_at = collection.updated_at = datetime.now(UTC)
    await collection_repository.update(collection)
    await uow.commit()


async def list_collection_placements(
    collection_id: UUID,
    auth: AuthUser,
    *,
    collection_repository: CollectionRepository,
    placement_repository: CollectionPlacementRepository,
    grant_repository: AccessGrantRepository,
) -> list[CollectionPlacementResponse]:
    collection = await get_accessible_collection(
        collection_id,
        auth,
        Permission.READ,
        collection_repository=collection_repository,
        placement_repository=placement_repository,
        grant_repository=grant_repository,
    )
    placements = await placement_repository.find_by_collection(collection.id)
    return [CollectionPlacementResponse.model_validate(placement) for placement in placements]


async def create_collection_placement(
    collection_id: UUID,
    dto: CreatePlacementDTO,
    auth: AuthUser,
    *,
    collection_repository: CollectionRepository,
    placement_repository: CollectionPlacementRepository,
    article_repository: ArticleRepository,
    grant_repository: AccessGrantRepository,
    uow: UnitOfWork,
) -> CollectionPlacementResponse:
    """Размещает статью или коллекцию в коллекции на заданной позиции."""

    collection = await get_accessible_collection(
        collection_id,
        auth,
        Permission.WRITE,
        collection_repository=collection_repository,
        placement_repository=placement_repository,
        grant_repository=grant_repository,
    )
    await placement_repository.lock_space_tree(collection.space_id)

    await _ensure_target_can_be_placed(
        collection,
        dto.target,
        auth,
        collection_repository=collection_repository,
        placement_repository=placement_repository,
        article_repository=article_repository,
        grant_repository=grant_repository,
    )

    if await placement_repository.find_target(collection.id, dto.target) is not None:
        raise CollectionTargetAlreadyPlacedError(
            f"Target {dto.target.id} is already placed in the collection."
        )

    siblings = await placement_repository.find_by_collection(collection.id)
    placement = CollectionPlacement(
        collection_id=collection.id,
        target=dto.target,
        rank=_resolve_rank(siblings, dto.position),
    )
    await placement_repository.create(placement)
    await uow.commit()

    return CollectionPlacementResponse.model_validate(placement)


async def _get_accessible_placement(
    placement_id: UUID,
    auth: AuthUser,
    *,
    collection_repository: CollectionRepository,
    placement_repository: CollectionPlacementRepository,
    grant_repository: AccessGrantRepository,
) -> tuple[CollectionPlacement, Collection]:
    placement = await placement_repository.read(placement_id)
    if placement is None:
        raise NotFoundError(f"Placement with ID {placement_id} not found.")

    collection = await get_accessible_collection(
        placement.collection_id,
        auth,
        Permission.WRITE,
        collection_repository=collection_repository,
        placement_repository=placement_repository,
        grant_repository=grant_repository,
    )
    return placement, collection


async def move_collection_placement(
    placement_id: UUID,
    dto: MovePlacementDTO,
    auth: AuthUser,
    *,
    collection_repository: CollectionRepository,
    placement_repository: CollectionPlacementRepository,
    article_repository: ArticleRepository,
    grant_repository: AccessGrantRepository,
    uow: UnitOfWork,
) -> CollectionPlacementResponse:
    """Перемещает элемент внутри коллекции или в другую коллекцию того же Space."""

    placement, source = await _get_accessible_placement(
        placement_id,
        auth,
        collection_repository=collection_repository,
        placement_repository=placement_repository,
        grant_repository=grant_repository,
    )
    await placement_repository.lock_space_tree(source.space_id)

    destination = source
    if dto.collection_id is not None and dto.collection_id != source.id:
        destination = await get_accessible_collection(
            dto.collection_id,
            auth,
            Permission.WRITE,
            collection_repository=collection_repository,
            placement_repository=placement_repository,
            grant_repository=grant_repository,
        )
        await _ensure_target_can_be_placed(
            destination,
            placement.target,
            auth,
            moving_placement_id=placement.id,
            collection_repository=collection_repository,
            placement_repository=placement_repository,
            article_repository=article_repository,
            grant_repository=grant_repository,
        )
        if await placement_repository.find_target(destination.id, placement.target) is not None:
            raise CollectionTargetAlreadyPlacedError(
                f"Target {placement.target.id} is already placed in the collection.",
            )

    siblings = [
        sibling
        for sibling in await placement_repository.find_by_collection(destination.id)
        if sibling.id != placement.id
    ]
    placement.collection_id = destination.id
    placement.rank = _resolve_rank(siblings, dto.position)
    placement.updated_at = datetime.now(UTC)

    await placement_repository.update(placement)
    await uow.commit()

    return CollectionPlacementResponse.model_validate(placement)


async def delete_collection_placement(
    placement_id: UUID,
    auth: AuthUser,
    *,
    collection_repository: CollectionRepository,
    placement_repository: CollectionPlacementRepository,
    grant_repository: AccessGrantRepository,
    uow: UnitOfWork,
) -> None:
    """Убирает элемент из коллекции, не удаляя саму статью или коллекцию."""

    placement, _ = await _get_accessible_placement(
        placement_id,
        auth,
        collection_repository=collection_repository,
        placement_repository=placement_repository,
        grant_repository=grant_repository,
    )
    await placement_repository.delete(placement.id)
    await uow.commit()


def _build_navigation(
    collections: Sequence[Collection],
    placements: Sequence[CollectionPlacement],
    articles: Sequence[ArticleSummaryResponse],
) -> SpaceNavigationResponse:
    """Собирает дерево навигации; размещения скрытых/архивных элементов пропускаются."""

    collections_by_id = {collection.id: collection for collection in collections}
    articles_by_id = {article.id: article for article in articles}

    children: defaultdict[UUID, list[CollectionPlacement]] = defaultdict(list)
    placed_collection_ids: set[UUID] = set()
    placed_article_ids: set[UUID] = set()

    for placement in sorted(placements, key=lambda placement: placement.rank):
        children[placement.collection_id].append(placement)
        match placement.target.type:
            case TargetType.COLLECTION:
                placed_collection_ids.add(placement.target.id)
            case TargetType.ARTICLE:
                placed_article_ids.add(placement.target.id)

    def article_node(article: ArticleSummaryResponse, placement_id: UUID | None = None) -> NavigationNode:
        return NavigationNode(
            type=TargetType.ARTICLE,
            id=article.id,
            placement_id=placement_id,
            title=article.title,
            slug=article.slug,
            status=article.status,
        )

    def collection_node(collection: Collection, placement_id: UUID | None = None) -> NavigationNode:
        node = NavigationNode(
            type=TargetType.COLLECTION,
            id=collection.id,
            placement_id=placement_id,
            title=collection.name,
            slug=collection.slug,
        )
        for placement in children[collection.id]:
            if placement.target.type is TargetType.COLLECTION and (
                child := collections_by_id.get(placement.target.id)
            ):
                node.children.append(collection_node(child, placement.id))
            elif placement.target.type is TargetType.ARTICLE and (
                article := articles_by_id.get(placement.target.id)
            ):
                node.children.append(article_node(article, placement.id))
        return node

    roots = sorted(
        (collection for collection in collections if collection.id not in placed_collection_ids),
        key=lambda collection: collection.name,
    )
    return SpaceNavigationResponse(
        collections=[collection_node(collection) for collection in roots],
        unplaced_articles=[
            article_node(article) for article in articles if article.id not in placed_article_ids
        ],
    )


async def get_space_navigation(
    space_id: UUID,
    auth: AuthUser,
    *,
    space_repository: SpaceRepository,
    collection_repository: CollectionRepository,
    placement_repository: CollectionPlacementRepository,
    article_query_repository: ArticleQueryRepository,
    grant_repository: AccessGrantRepository,
) -> SpaceNavigationResponse:
    """
    Дерево навигации Space (READ на Space).

    При allow-only ACL READ на Space даёт чтение всех его коллекций и опубликованных статей,
    поэтому дерево не фильтруется по отдельным grants; черновики видны только при WRITE.
    """

    space = await get_accessible_space(
        space_id,
        auth,
        Permission.READ,
        space_repository=space_repository,
        grant_repository=grant_repository,
    )
    permissions = await resolve_permissions(
        auth,
        (Resource(type="space", id=space.id),),
        grant_repository=grant_repository,
    )

    collections = await collection_repository.find_by_space(space.id)
    placements = await placement_repository.find_by_collections([collection.id for collection in collections])
    articles = await article_query_repository.find_space_articles(
        space.id,
        include_drafts=Permission.WRITE in permissions,
    )
    return _build_navigation(collections, placements, articles)
