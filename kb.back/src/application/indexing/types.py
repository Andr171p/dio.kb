from collections.abc import AsyncIterator, Awaitable, Callable, Sequence
from contextlib import AbstractAsyncContextManager
from enum import StrEnum
from uuid import UUID

from src.domain.articles.models import PublishedArticle

from .checkpoint import IndexCheckpoint
from .commands import IndexCommand
from .models import IndexedChunk

type OpenMedia = Callable[[UUID], AbstractAsyncContextManager[AsyncIterator[bytes]]]

type EnqueueIndexCommand = Callable[[IndexCommand], Awaitable[UUID]]

# ``ConfirmIndexed`` обязан выполнить одну атомарную операцию БД:
#
# 1. Найти статью в указанной организации.
# 2. Проверить, что она всё ещё опубликована.
# 3. Проверить ``revision_id`` и её версию (``version``).
# 4. Сохранить checkpoint.
# 5. Выполнить commit.
#
# True - после успешного commit.
type ConfirmIndexed = Callable[[IndexCheckpoint], Awaitable[bool]]

# LoadPublication(organization_id, article_id) возвращает (Article, ArticleRevision)
# только для опубликованной статьи.
type LoadPublication = Callable[[UUID, UUID], Awaitable[PublishedArticle | None]]

# обеспечивает сериализацию финальных операций над одной статьёй между всеми экземплярами indexing workers.
type LockArticleIndex = Callable[[UUID, UUID], AbstractAsyncContextManager[None]]

type PrepareArticleChunks = Callable[[PublishedArticle], Awaitable[Sequence[IndexedChunk]]]


class IndexOutcome(StrEnum):
    INDEXED = "indexed"
    DELETED = "deleted"
    UNCHANGED = "unchanged"
    SUPERSEDED = "superseded"


__all__ = [
    "ConfirmIndexed",
    "EnqueueIndexCommand",
    "IndexOutcome",
    "LoadPublication",
    "LockArticleIndex",
    "OpenMedia",
    "PrepareArticleChunks",
]
