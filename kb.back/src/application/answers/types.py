from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from uuid import UUID

from src.application.auth.dtos import AuthUser
from src.application.search.dtos import SearchRequest, SearchResponse

from .dtos import AnswerDraft, AnswerSource
from .models import AnswerStage, AnswerUsage


@dataclass(frozen=True, slots=True)
class GeneratedAnswer:
    draft: AnswerDraft
    usage: AnswerUsage | None
    provider: str
    model_id: str
    generation_ms: int


type SearchForAnswer = Callable[[UUID, AuthUser, SearchRequest], Awaitable[SearchResponse]]

type GenerateAnswer = Callable[[str, Sequence[AnswerSource]], Awaitable[GeneratedAnswer]]

type ReportProgress = Callable[[UUID, AnswerStage, dict[str, int]], Awaitable[None]]

type NotifyAnswerProgress = Callable[[UUID], Awaitable[None]]
