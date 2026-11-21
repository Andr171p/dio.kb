from uuid import UUID

from sqlalchemy import and_, not_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.application.indexing.reconciliation import ReconciliationQuery
from src.domain.articles.models import PublishedArticle
from src.infra.database.models import ArticleOrm, ArticleRevisionOrm, IndexCheckpointOrm, SpaceOrm
from src.infra.database.repositories.article import ArticleMapper
from src.infra.database.repositories.revision import ArticleRevisionMapper


async def load_publication(
    organization_id: UUID,
    article_id: UUID,
    *,
    sessionmaker: async_sessionmaker[AsyncSession],
) -> PublishedArticle | None:
    """Читает текущую опубликованную редакцию статьи."""

    stmt = (
        select(ArticleOrm, ArticleRevisionOrm)
        .join(
            ArticleRevisionOrm,
            and_(
                ArticleRevisionOrm.id == ArticleOrm.published_revision_id,
                ArticleRevisionOrm.article_id == ArticleOrm.id,
            ),
        )
        .join(
            SpaceOrm,
            and_(
                SpaceOrm.id == ArticleOrm.space_id,
                SpaceOrm.organization_id == ArticleOrm.organization_id,
            ),
        )
        .where(
            ArticleOrm.id == article_id,
            ArticleOrm.organization_id == organization_id,
            ArticleOrm.deleted_at.is_(None),
            SpaceOrm.deleted_at.is_(None),
        )
    )

    async with sessionmaker() as session:
        row = (await session.execute(stmt)).one_or_none()

    if row is None:
        return None

    article, revision = row

    return ArticleMapper.from_model(article), ArticleRevisionMapper.from_model(revision)


async def find_candidates(
    query: ReconciliationQuery,
    *,
    sessionmaker: async_sessionmaker[AsyncSession],
) -> tuple[UUID, ...]:
    """Находит статьи с устаревшей или отсутствующей проекцией."""

    published = and_(
        ArticleOrm.deleted_at.is_(None),
        ArticleOrm.published_revision_id.is_not(None),
        SpaceOrm.deleted_at.is_(None),
    )

    has_checkpoint = IndexCheckpointOrm.article_id.is_not(None)

    changed = or_(
        IndexCheckpointOrm.revision_id.is_distinct_from(ArticleOrm.published_revision_id),
        IndexCheckpointOrm.space_id.is_distinct_from(ArticleOrm.space_id),
    )

    stale = or_(
        and_(published, or_(not_(has_checkpoint), changed)),
        and_(not_(published), has_checkpoint),
    )

    # noinspection PyUnreachableCode
    match query.mode:
        case "stale":
            condition = stale
        case "rebuild":
            condition = or_(published, has_checkpoint)
        case _:
            raise ValueError(f"Unsupported reconciliation mode: {query.mode}")

    stmt = (
        select(ArticleOrm.id)
        .join(
            SpaceOrm,
            and_(
                SpaceOrm.id == ArticleOrm.space_id,
                SpaceOrm.organization_id == ArticleOrm.organization_id,
            ),
        )
        .outerjoin(
            IndexCheckpointOrm,
            and_(
                IndexCheckpointOrm.article_id == ArticleOrm.id,
                IndexCheckpointOrm.generation == query.generation,
            ),
        )
        .where(ArticleOrm.organization_id == query.organization_id, condition)
        .order_by(ArticleOrm.id)
        .limit(query.limit)
    )

    if query.after_id is not None:
        stmt = stmt.where(ArticleOrm.id > query.after_id)

    async with sessionmaker() as session:
        return tuple(await session.scalars(stmt))


__all__ = ["find_candidates", "load_publication"]
