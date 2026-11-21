from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ChunkHit:
    """Найденный фрагмент статьи."""

    chunk_id: UUID
    article_id: UUID
    revision_id: UUID

    score: float
    markdown: str
    heading_path: tuple[str, ...]
    anchor: str | None = None


@dataclass(frozen=True, slots=True)
class ArticleMatch:
    """Кандидат, найденный поисковым движком. Он ещё не прошёл финальную проверку ``READ``."""

    article_id: UUID
    score: float
    hits: tuple[ChunkHit, ...]
