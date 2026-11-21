from datetime import datetime
from uuid import UUID

from ddf.infra.database.sqlalchemy import Base
from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, Uuid, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column


class GapSignalOrm(Base):
    __tablename__ = "gap_signals"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "source_type",
            "source_id",
            "kind",
            name="uq_gap_signals_source",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    organization_id: Mapped[UUID] = mapped_column(index=True)
    kind: Mapped[str] = mapped_column(String(64))
    source_type: Mapped[str] = mapped_column(String(64))
    source_id: Mapped[UUID]
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    answer_id: Mapped[UUID | None]
    article_ids: Mapped[list[UUID] | None] = mapped_column(ARRAY(Uuid()))
    topic_hint: Mapped[str | None] = mapped_column(String(255))
    space_id: Mapped[UUID | None]
    metadata_json: Mapped[dict | None] = mapped_column("metadata", JSONB)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class KnowledgeGapOrm(Base):
    __tablename__ = "knowledge_gaps"
    __table_args__ = (
        UniqueConstraint("organization_id", "grouping_key", name="uq_knowledge_gaps_grouping"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    organization_id: Mapped[UUID] = mapped_column(index=True)
    space_id: Mapped[UUID | None] = mapped_column(index=True)
    grouping_key: Mapped[str] = mapped_column(String(128))
    title: Mapped[str] = mapped_column(String(500))
    kind: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), index=True)
    owner_id: Mapped[UUID | None]
    related_article_id: Mapped[UUID | None]
    resolution_note: Mapped[str | None] = mapped_column(Text)
    rationale: Mapped[str | None] = mapped_column(Text)
    version: Mapped[int] = mapped_column(default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class KnowledgeGapSignalOrm(Base):
    __tablename__ = "knowledge_gap_signals"
    __table_args__ = (UniqueConstraint("gap_id", "signal_id", name="uq_knowledge_gap_signals"),)

    gap_id: Mapped[UUID] = mapped_column(ForeignKey("knowledge_gaps.id", ondelete="CASCADE"), primary_key=True)
    signal_id: Mapped[UUID] = mapped_column(ForeignKey("gap_signals.id", ondelete="CASCADE"), primary_key=True)
    organization_id: Mapped[UUID] = mapped_column(index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
