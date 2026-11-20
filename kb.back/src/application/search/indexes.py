from typing import Protocol

from collections.abc import Collection, Sequence
from dataclasses import dataclass
from uuid import UUID

from .access import SearchScope
from .models import ArticleMatch


@dataclass(frozen=True, slots=True)
class SearchOptions:
    """Дополнительные параметры поиска."""

    candidates_limit: int
    max_hits_per_article: int


class SuggestionIndex(Protocol):
    """Быстрый лексический поиск по заголовкам статей."""

    async def suggest(
        self,
        query: str,
        *,
        scope: SearchScope,
        space_ids: Collection[UUID] | None,
        limit: int,
    ) -> Sequence[UUID]:
        """Идентификаторы статей по убыванию релевантности."""


class SearchIndexReader(Protocol):
    """Восстанавливаемая поисковая проекция опубликованных статей."""

    @property
    def generation(self) -> str:
        """Идентификатор поколения поисковой проекции."""

    async def search(
        self,
        *,
        query: str,
        query_embedding: Sequence[float],
        scope: SearchScope,
        space_ids: Sequence[UUID],
        options: SearchOptions,
    ) -> Sequence[ArticleMatch]:
        """Гибридный поиск строго внутри ``scope``, сгруппированный по статьям."""


__all__ = ["SearchIndexReader", "SearchOptions", "SuggestionIndex"]
