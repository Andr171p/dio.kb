
"""
Лексический поиск подсказок по заголовкам опубликованных статей DIOS KB.

Используется для autocomplete при вводе поискового запроса. В отличие от
полноценного гибридного поиска, не использует embeddings и Qdrant:
подсказки формируются непосредственно в PostgreSQL.

Алгоритм поиска:
    1. Ограничивает кандидатов организацией, активными пространствами
       и предварительно разрешёнными ресурсами из ``SearchScope``.
    2. Ищет совпадения по заголовкам опубликованных редакций статей.
    3. Комбинирует несколько стратегий поиска по приоритету:
       - Exact: полное совпадение без учёта регистра.
       - Prefix: совпадение с началом заголовка.
       - FTS: полнотекстовый поиск с учётом русской морфологии.
       - Substring: вхождение запроса в произвольную часть заголовка.
       - Fuzzy: поиск похожих написаний через pg_trgm.
    4. Ранжирует совпадения по типу, триграммной близости и заголовку.
    5. Возвращает ограниченный список ``article_id`` в порядке релевантности.

Производительность:
    - Prefix search использует индекс по lower(title).
    - FTS использует GIN-индекс по to_tsvector('russian', title).
    - Substring и fuzzy matching используют GIN-индекс gin_trgm_ops.
    - Для коротких запросов дорогие стратегии отключаются.
    - Поиск выполняется только по заголовкам, без анализа содержимого статей.

Безопасность:
    ``SearchScope`` используется исключительно для предварительной фильтрации.
    Он может содержать устаревшие разрешения и не является окончательным
    подтверждением доступа пользователя.

    Поэтому возвращаемые ``article_id`` считаются кандидатами. Application
    обязан повторно проверить актуальные READ permissions, организацию,
    пространство и состояние публикации через ``ArticleQueryRepository``
    перед формированием ``SuggestionsResponse``.

    Названия статей для ответа также берутся из PostgreSQL после
    финальной проверки, а не из результатов предварительного поиска.

Ограничения:
    - Поиск выполняется только по заголовкам опубликованных редакций.
    - Не ищет по Markdown, OCR, вложениям и содержимому документов.
    - Не исправляет запрос автоматически: fuzzy matching лишь находит
      близкие написания.
    - Релевантность определяется эвристическим ранжированием, а не LLM.

Реализация зависит от PostgreSQL и расширения pg_trgm.
"""


from collections.abc import Collection, Sequence
from uuid import UUID

from sqlalchemy import and_, case, func, literal_column, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.search.access import SearchScope
from src.infra.database.models import ArticleOrm, ArticleRevisionOrm, SpaceOrm

_FTS_CONFIG = literal_column("'russian'::regconfig")

_SHORT_QUERY_LENGTH = 3
_MIN_FUZZY_MATCHING_QUERY_LENGTH = 4


def _escape_like(value: str) -> str:
    """Экранирует специальные символы SQL LIKE."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


class SqlAlchemySuggestionIndex:
    """Лексический поиск по заголовкам опубликованных статей."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def suggest(
        self,
        query: str,
        *,
        scope: SearchScope,
        space_ids: Collection[UUID] | None,
        limit: int,
    ) -> Sequence[UUID]:
        query = query.strip()

        if not query or limit < 1:
            return ()

        if space_ids is not None and not space_ids:
            return ()

        spaces = [resource.id for resource in scope.resources if resource.type == "space"]
        articles = [resource.id for resource in scope.resources if resource.type == "article"]

        if not spaces and not articles:
            return ()

        title = ArticleRevisionOrm.title
        normalized = query.lower()

        # Prefix search: быстрые подсказки во время ввода.
        title_lower = func.lower(title)
        exact = title_lower == normalized
        prefix = title_lower.like(f"{_escape_like(normalized)}%", escape="\\")

        # FTS: поиск слов с нормализацией словоформ.
        title_vector = func.to_tsvector(_FTS_CONFIG, title)
        tsquery = func.plainto_tsquery(_FTS_CONFIG, query)
        fts = title_vector.bool_op("@@")(tsquery)

        conditions = [prefix, fts]
        ranks = [(exact, 0), (prefix, 1), (fts, 2)]

        # На коротких строках не используем substring из-за низкой селективности триграмм.
        if len(query) >= _SHORT_QUERY_LENGTH:
            contains = title.ilike(f"%{_escape_like(query)}%", escape="\\")
            conditions.append(contains)
            ranks.append((contains, 3))

        # Fuzzy matching с помощью pg_trgm.
        if len(query) >= _MIN_FUZZY_MATCHING_QUERY_LENGTH:
            # title %> query эквивалентно query <% title.
            fuzzy = title.bool_op("%>")(query)
            conditions.append(fuzzy)

        priority = case(*ranks, else_=4)

        stmt = (
            select(ArticleOrm.id)
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
                ArticleOrm.organization_id == scope.organization_id,
                ArticleOrm.deleted_at.is_(None),
                SpaceOrm.deleted_at.is_(None),
                or_(
                    ArticleOrm.space_id.in_(spaces),
                    ArticleOrm.id.in_(articles),
                ),
                or_(*conditions),
            )
        )

        if space_ids is not None:
            stmt = stmt.where(ArticleOrm.space_id.in_(space_ids))

        stmt = stmt.order_by(
            priority,
            func.word_similarity(query, title).desc(),
            title,
            ArticleOrm.id,
        ).limit(limit)

        return tuple(await self._session.scalars(stmt))


__all__ = ["SqlAlchemySuggestionIndex"]
