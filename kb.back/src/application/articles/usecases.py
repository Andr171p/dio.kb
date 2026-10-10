from uuid import UUID

from ddf.application.exceptions import NotFoundError
from ddf.application.outbox import OutboxStore
from ddf.application.uow import UnitOfWork

from src.application.access import AccessGrantRepository, Permission, Resource, resolve_permissions
from src.application.auth import AuthUser
from src.application.outbox import save_events_to_outbox
from src.application.spaces.access import get_accessible_space
from src.application.spaces.repositories import SpaceRepository
from src.domain.articles import logic
from src.domain.articles.models import Article, ArticleRevision

from .access import get_accessible_article, resolve_article_permissions
from .dtos import (
    ArticleDetailResponse,
    ArticleResponse,
    ArticleRevisionResponse,
    ArticleRevisionSummaryResponse,
    ArticleSummaryResponse,
    CreateArticleDTO,
    PublishArticleDTO,
    RestoreArticleRevisionDTO,
    ReviseArticleDTO,
)
from .repositories import ArticleQueryRepository, ArticleRepository, ArticleRevisionRepository


async def _to_detail(
    article: Article,
    revision: ArticleRevision,
    auth: AuthUser,
    *,
    grant_repository: AccessGrantRepository,
) -> ArticleDetailResponse:
    return ArticleDetailResponse(
        article=ArticleResponse.model_validate(article),
        revision=ArticleRevisionResponse.model_validate(revision),
        permissions=await resolve_article_permissions(article, auth, grant_repository=grant_repository),
    )


async def _read_revision(
    article: Article,
    revision_id: UUID,
    *,
    revision_repository: ArticleRevisionRepository,
) -> ArticleRevision:
    revision = await revision_repository.read(revision_id)

    if revision is None or revision.article_id != article.id:
        raise NotFoundError(f"Revision with ID {revision_id} not found.")

    return revision


async def create_article(
    space_id: UUID,
    dto: CreateArticleDTO,
    auth: AuthUser,
    *,
    space_repository: SpaceRepository,
    article_repository: ArticleRepository,
    revision_repository: ArticleRevisionRepository,
    grant_repository: AccessGrantRepository,
    uow: UnitOfWork,
) -> ArticleDetailResponse:
    """Создаёт черновик статьи с первой редакцией (WRITE на Space)."""

    await get_accessible_space(
        space_id,
        auth,
        Permission.WRITE,
        space_repository=space_repository,
        grant_repository=grant_repository,
    )

    article, revision = logic.create_article_with_first_revision(
        organization_id=auth.user.organization_id,
        space_id=space_id,
        author_id=auth.user.id,
        slug=dto.slug,
        title=dto.title,
        content=dto.content,
        summary=dto.summary,
    )

    await article_repository.create(article)
    await revision_repository.create(revision)
    await uow.commit()

    return await _to_detail(article, revision, auth, grant_repository=grant_repository)


async def list_space_articles(
    space_id: UUID,
    auth: AuthUser,
    *,
    space_repository: SpaceRepository,
    article_query_repository: ArticleQueryRepository,
    grant_repository: AccessGrantRepository,
) -> list[ArticleSummaryResponse]:
    """Статьи пространства; черновики видны только при WRITE на Space."""

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

    articles = await article_query_repository.find_space_articles(
        space.id,
        include_drafts=Permission.WRITE in permissions,
    )
    return list(articles)


async def get_published_article(
    article_id: UUID,
    auth: AuthUser,
    *,
    article_repository: ArticleRepository,
    revision_repository: ArticleRevisionRepository,
    grant_repository: AccessGrantRepository,
) -> ArticleDetailResponse:
    """Опубликованная редакция статьи для читателя (READ)."""

    article = await get_accessible_article(
        article_id,
        auth,
        Permission.READ,
        article_repository=article_repository,
        grant_repository=grant_repository,
    )

    if not article.is_published or article.published_revision_id is None:
        raise NotFoundError(f"Published article with ID {article_id} not found.")

    revision = await _read_revision(
        article,
        article.published_revision_id,
        revision_repository=revision_repository,
    )
    return await _to_detail(article, revision, auth, grant_repository=grant_repository)


async def get_published_article_by_slug(
    space_id: UUID,
    slug: str,
    auth: AuthUser,
    *,
    article_repository: ArticleRepository,
    revision_repository: ArticleRevisionRepository,
    grant_repository: AccessGrantRepository,
) -> ArticleDetailResponse:
    article = await article_repository.find_by_slug(space_id, slug)

    if article is None:
        raise NotFoundError(f"Article {slug!r} not found.")

    return await get_published_article(
        article.id,
        auth,
        article_repository=article_repository,
        revision_repository=revision_repository,
        grant_repository=grant_repository,
    )


async def get_article_draft(
    article_id: UUID,
    auth: AuthUser,
    *,
    article_repository: ArticleRepository,
    revision_repository: ArticleRevisionRepository,
    grant_repository: AccessGrantRepository,
) -> ArticleDetailResponse:
    """Текущая редакторская версия (WRITE)."""

    article = await get_accessible_article(
        article_id,
        auth,
        Permission.WRITE,
        article_repository=article_repository,
        grant_repository=grant_repository,
    )
    revision = await _read_revision(
        article, article.current_revision_id, revision_repository=revision_repository
    )
    return await _to_detail(article, revision, auth, grant_repository=grant_repository)


async def list_article_revisions(
    article_id: UUID,
    auth: AuthUser,
    *,
    article_repository: ArticleRepository,
    revision_repository: ArticleRevisionRepository,
    grant_repository: AccessGrantRepository,
) -> list[ArticleRevisionSummaryResponse]:
    article = await get_accessible_article(
        article_id,
        auth,
        Permission.WRITE,
        article_repository=article_repository,
        grant_repository=grant_repository,
    )
    revisions = await revision_repository.find_by_article(article.id)
    return [ArticleRevisionSummaryResponse.model_validate(revision) for revision in revisions]


async def get_article_revision(
    article_id: UUID,
    revision_id: UUID,
    auth: AuthUser,
    *,
    article_repository: ArticleRepository,
    revision_repository: ArticleRevisionRepository,
    grant_repository: AccessGrantRepository,
) -> ArticleRevisionResponse:
    article = await get_accessible_article(
        article_id,
        auth,
        Permission.WRITE,
        article_repository=article_repository,
        grant_repository=grant_repository,
    )
    revision = await _read_revision(article, revision_id, revision_repository=revision_repository)
    return ArticleRevisionResponse.model_validate(revision)


async def revise_article(
    article_id: UUID,
    dto: ReviseArticleDTO,
    auth: AuthUser,
    *,
    article_repository: ArticleRepository,
    revision_repository: ArticleRevisionRepository,
    grant_repository: AccessGrantRepository,
    uow: UnitOfWork,
) -> ArticleDetailResponse:
    """Создаёт новую редакцию; опубликованная версия и поисковый индекс не меняются до публикации."""

    article = await get_accessible_article(
        article_id,
        auth,
        Permission.WRITE,
        article_repository=article_repository,
        grant_repository=grant_repository,
        with_lock=True,
    )

    revision = logic.revise_article(
        article,
        based_on_revision_id=dto.expected_revision_id,
        author_id=auth.user.id,
        title=dto.title,
        content=dto.content,
        summary=dto.summary,
        change_note=dto.change_note,
    )

    await revision_repository.create(revision)
    await article_repository.update(article)
    await uow.commit()

    return await _to_detail(article, revision, auth, grant_repository=grant_repository)


async def restore_article_revision(
    article_id: UUID,
    source_revision_id: UUID,
    dto: RestoreArticleRevisionDTO,
    auth: AuthUser,
    *,
    article_repository: ArticleRepository,
    revision_repository: ArticleRevisionRepository,
    grant_repository: AccessGrantRepository,
    uow: UnitOfWork,
) -> ArticleDetailResponse:
    """Создаёт новую редакцию с содержимым исторической; история не переписывается."""

    article = await get_accessible_article(
        article_id,
        auth,
        Permission.WRITE,
        article_repository=article_repository,
        grant_repository=grant_repository,
        with_lock=True,
    )
    source = await _read_revision(article, source_revision_id, revision_repository=revision_repository)

    revision = logic.restore_article_revision(
        article,
        source,
        based_on_revision_id=dto.expected_revision_id,
        author_id=auth.user.id,
        change_note=dto.change_note,
    )

    await revision_repository.create(revision)
    await article_repository.update(article)
    await uow.commit()

    return await _to_detail(article, revision, auth, grant_repository=grant_repository)


async def publish_article(
    article_id: UUID,
    dto: PublishArticleDTO,
    auth: AuthUser,
    *,
    article_repository: ArticleRepository,
    grant_repository: AccessGrantRepository,
    outbox: OutboxStore,
    uow: UnitOfWork,
) -> ArticleResponse:
    """Публикует текущую редакцию; индексация запускается асинхронно через outbox."""

    article = await get_accessible_article(
        article_id,
        auth,
        Permission.PUBLISH,
        article_repository=article_repository,
        grant_repository=grant_repository,
        with_lock=True,
    )

    article.publish(dto.revision_id)

    await article_repository.update(article)
    await save_events_to_outbox(outbox, article)
    await uow.commit()

    return ArticleResponse.model_validate(article)


async def unpublish_article(
    article_id: UUID,
    auth: AuthUser,
    *,
    article_repository: ArticleRepository,
    grant_repository: AccessGrantRepository,
    outbox: OutboxStore,
    uow: UnitOfWork,
) -> ArticleResponse:
    """Снимает публикацию: недоступна читателям сразу, из индекса удаляется асинхронно."""

    article = await get_accessible_article(
        article_id,
        auth,
        Permission.PUBLISH,
        article_repository=article_repository,
        grant_repository=grant_repository,
        with_lock=True,
    )

    article.unpublish()

    await article_repository.update(article)
    await save_events_to_outbox(outbox, article)
    await uow.commit()

    return ArticleResponse.model_validate(article)


async def archive_article(
    article_id: UUID,
    auth: AuthUser,
    *,
    article_repository: ArticleRepository,
    grant_repository: AccessGrantRepository,
    outbox: OutboxStore,
    uow: UnitOfWork,
) -> None:
    article = await get_accessible_article(
        article_id,
        auth,
        Permission.ARCHIVE,
        article_repository=article_repository,
        grant_repository=grant_repository,
        with_lock=True,
    )

    article.archive()

    await article_repository.update(article)
    await save_events_to_outbox(outbox, article)
    await uow.commit()


async def restore_article(
    article_id: UUID,
    auth: AuthUser,
    *,
    article_repository: ArticleRepository,
    grant_repository: AccessGrantRepository,
    uow: UnitOfWork,
) -> ArticleResponse:
    """Возвращает статью из архива черновиком (повторная публикация — явное действие)."""

    article = await get_accessible_article(
        article_id,
        auth,
        Permission.ARCHIVE,
        article_repository=article_repository,
        grant_repository=grant_repository,
        with_lock=True,
    )

    article.restore()

    await article_repository.update(article)
    await uow.commit()

    return ArticleResponse.model_validate(article)
