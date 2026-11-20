from datetime import datetime
from uuid import UUID

from ddf.infra.database.sqlalchemy import Base
from sqlalchemy import (
    ARRAY,
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column


class ImageAnalysisOrm(Base):
    __tablename__ = "image_analysis"

    media_id: Mapped[UUID] = mapped_column(primary_key=True)
    version: Mapped[str] = mapped_column(String(255), primary_key=True)
    text: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ArticleIndexStateOrm(Base):
    __tablename__ = "article_index_states"

    article_id: Mapped[UUID] = mapped_column(ForeignKey("articles.id"), primary_key=True)
    revision_id: Mapped[UUID | None]
    index_name: Mapped[str] = mapped_column(String(255))
    chunk_count: Mapped[int]
    failed_media_ids: Mapped[list[UUID]] = mapped_column(ARRAY(PG_UUID(as_uuid=True)), server_default="{}")
    indexed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
