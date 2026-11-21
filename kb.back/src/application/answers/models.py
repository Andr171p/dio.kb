from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .dtos import AnswerResponse, AnswerStatus


class AnswerRunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AnswerStage(StrEnum):
    RETRIEVAL = "retrieval"
    CONTEXT_PREPARATION = "context_preparation"
    GENERATION = "generation"
    VALIDATION = "validation"


class AnswerUsage(BaseModel):
    model_config = ConfigDict(frozen=True)

    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    cached_input_tokens: int = Field(default=0, ge=0)
    reasoning_tokens: int | None = Field(default=None, ge=0)
    estimated_cost_usd: Decimal | None = None


class AnswerRun(BaseModel):
    """Долговременная запись попытки, не доменный агрегат."""

    id: UUID
    organization_id: UUID
    principal_id: UUID
    principal_type: str
    status: AnswerRunStatus
    stage: AnswerStage | None = None
    stage_sequence: int = 0

    question: str | None = None
    space_ids: list[UUID] | None = None
    actor_roles: list[str] = Field(default_factory=list)
    answer_status: AnswerStatus | None = None
    response: AnswerResponse | None = None

    provider: str | None = None
    model_id: str | None = None
    prompt_version: str | None = None
    retrieval_version: str | None = None
    usage: AnswerUsage | None = None

    results_count: int | None = None
    sources_count: int | None = None
    latency_ms: int | None = None
    error_code: str | None = None
    idempotency_key: str | None = None

    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None


class AnswerProgressEvent(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    answer_id: UUID
    sequence: int = Field(ge=0)
    event: str
    occurred_at: datetime
    status: str
    stage: str | None = None
    results_count: int | None = None
    sources_count: int | None = None
    error_code: str | None = None
