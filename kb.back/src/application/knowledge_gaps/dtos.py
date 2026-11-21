from dataclasses import dataclass
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from src.domain.knowledge_gaps.types import GapKind, GapStatus


class GapDTO(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        validate_by_name=True,
        serialize_by_alias=True,
        extra="forbid",
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class GapCandidate:
    organization_id: UUID
    grouping_key: str
    title: str
    suggested_kind: GapKind
    signal_ids: tuple[UUID, ...]
    related_article_ids: tuple[UUID, ...] = ()
    rationale: str = ""
    space_id: UUID | None = None


class KnowledgeGapResponse(GapDTO):
    id: UUID
    organization_id: UUID
    grouping_key: str
    title: str
    space_id: UUID | None = None
    kind: GapKind
    status: GapStatus
    owner_id: UUID | None = None
    related_article_id: UUID | None = None
    resolution_note: str | None = None
    rationale: str | None = None
    signal_count: int = 0


class KnowledgeGapListResponse(GapDTO):
    items: list[KnowledgeGapResponse]


class PatchKnowledgeGapRequest(GapDTO):
    kind: GapKind | None = None
    owner_id: UUID | None = None
    related_article_id: UUID | None = None


class ResolveKnowledgeGapRequest(GapDTO):
    note: str = Field(min_length=1, max_length=2000)


class DismissKnowledgeGapRequest(GapDTO):
    reason: str = Field(min_length=1, max_length=2000)
