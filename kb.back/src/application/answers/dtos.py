from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel


class AnswerStatus(StrEnum):
    ANSWERED = "answered"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    CONFLICTING_EVIDENCE = "conflicting_evidence"


class FeedbackReason(StrEnum):
    NO_SOLUTION = "no_solution"
    INCORRECT = "incorrect"
    INCOMPLETE = "incomplete"
    OUTDATED = "outdated"
    IRRELEVANT_SOURCES = "irrelevant_sources"
    OTHER = "other"


class AnswerDTO(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        validate_by_name=True,
        serialize_by_alias=True,
        extra="forbid",
    )


class AnswerRequest(AnswerDTO):
    question: str = Field(min_length=2, max_length=2000)
    space_ids: list[UUID] | None = Field(default=None, max_length=100)


class AnswerSource(AnswerDTO):
    id: str
    article_id: UUID
    revision_id: UUID
    chunk_id: UUID
    title: str
    url: str
    excerpt: str
    anchor: str | None = None


class AnswerBlock(AnswerDTO):
    markdown: str
    citations: list[str] = Field(default_factory=list)


class AnswerDraft(BaseModel):
    """Недоверенный результат LLM до validation."""

    status: AnswerStatus
    blocks: list[AnswerBlock] = Field(default_factory=list)
    missing_context: list[str] = Field(default_factory=list)


class AnswerResponse(AnswerDTO):
    id: UUID
    status: AnswerStatus
    blocks: list[AnswerBlock]
    sources: list[AnswerSource]
    missing_context: list[str] = Field(default_factory=list)


class AnswerAccepted(AnswerDTO):
    id: UUID
    status: str
    events_url: str
    result_url: str


class AnswerFeedbackRequest(AnswerDTO):
    helpful: bool
    reason: FeedbackReason | None = None
    comment: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def validate_reason(self) -> AnswerFeedbackRequest:
        if self.helpful and self.reason is not None:
            raise ValueError("Reason is only allowed for negative feedback")
        return self


class AnswerFeedbackResponse(AnswerDTO):
    answer_id: UUID
    helpful: bool
    reason: FeedbackReason | None = None
    comment: str | None = None
