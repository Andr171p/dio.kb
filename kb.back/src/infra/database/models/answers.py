from datetime import datetime
from decimal import Decimal
from uuid import UUID

from ddf.infra.database.sqlalchemy import Base
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, Uuid, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column


class AnswerRunOrm(Base):
    __tablename__ = "answer_runs"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "principal_id",
            "idempotency_key",
            name="uq_answer_runs_idempotency",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    organization_id: Mapped[UUID] = mapped_column(index=True)
    principal_id: Mapped[UUID]
    principal_type: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32), index=True)
    stage: Mapped[str | None] = mapped_column(String(32))
    stage_sequence: Mapped[int] = mapped_column(Integer, default=0)

    question: Mapped[str | None] = mapped_column(Text)
    space_ids: Mapped[list[UUID] | None] = mapped_column(ARRAY(Uuid()))
    actor_roles: Mapped[list[str]] = mapped_column(ARRAY(String), server_default="{}")
    answer_status: Mapped[str | None] = mapped_column(String(64))
    response: Mapped[dict | None] = mapped_column(JSONB)

    provider: Mapped[str | None] = mapped_column(String(64))
    model_id: Mapped[str | None] = mapped_column(String(128))
    prompt_version: Mapped[str | None] = mapped_column(String(64))
    retrieval_version: Mapped[str | None] = mapped_column(String(64))
    usage: Mapped[dict | None] = mapped_column(JSONB)
    estimated_cost_usd: Mapped[Decimal | None] = mapped_column(Numeric(12, 6))
    metrics: Mapped[dict | None] = mapped_column(JSONB)

    results_count: Mapped[int | None] = mapped_column(Integer)
    sources_count: Mapped[int | None] = mapped_column(Integer)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    error_code: Mapped[str | None] = mapped_column(String(64))
    idempotency_key: Mapped[str | None] = mapped_column(String(128))

    lease_owner: Mapped[str | None] = mapped_column(String(128))
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AnswerFeedbackOrm(Base):
    __tablename__ = "answer_feedback"
    __table_args__ = (UniqueConstraint("answer_id", "actor_id", name="uq_answer_feedback_actor"),)

    id: Mapped[UUID] = mapped_column(primary_key=True)
    answer_id: Mapped[UUID] = mapped_column(ForeignKey("answer_runs.id", ondelete="CASCADE"))
    organization_id: Mapped[UUID] = mapped_column(index=True)
    actor_id: Mapped[UUID]
    helpful: Mapped[bool] = mapped_column(Boolean)
    reason: Mapped[str | None] = mapped_column(String(64))
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
