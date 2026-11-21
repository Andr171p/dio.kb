from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class GapSignalKind(StrEnum):
    ANSWER_INSUFFICIENT = "answer_insufficient"
    ANSWER_NOT_HELPFUL = "answer_not_helpful"
    SOURCES_CONFLICT = "sources_conflict"
    SEARCH_NO_RESULTS = "search_no_results"
    ARTICLE_OUTDATED = "article_outdated"


class GapSignalSourceType(StrEnum):
    ANSWER_RUN = "answer_run"
    ANSWER_FEEDBACK = "answer_feedback"


@dataclass(frozen=True, slots=True, kw_only=True)
class GapSignal:
    id: UUID
    organization_id: UUID
    kind: GapSignalKind
    source_type: GapSignalSourceType
    source_id: UUID
    occurred_at: datetime
    answer_id: UUID | None = None
    article_ids: tuple[UUID, ...] = ()
    topic_hint: str | None = None
    space_id: UUID | None = None
    processed_at: datetime | None = None
