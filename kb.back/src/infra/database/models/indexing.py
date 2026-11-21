from datetime import datetime
from uuid import UUID

from ddf.infra.database.sqlalchemy import Base
from sqlalchemy import ARRAY, REAL, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column


class ImageAnalysisOrm(Base):
    __tablename__ = "image_analysis"

    media_id: Mapped[UUID] = mapped_column(primary_key=True)
    version: Mapped[str] = mapped_column(String(255), primary_key=True)
    text: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EmbeddingOrm(Base):
    __tablename__ = "embeddings"

    content_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    version: Mapped[str] = mapped_column(String(255), primary_key=True)
    vector: Mapped[list[float]] = mapped_column(ARRAY(REAL), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class IndexCheckpointOrm(Base):
    __tablename__ = "index_checkpoints"

    article_id: Mapped[UUID] = mapped_column(ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True)
    generation: Mapped[str] = mapped_column(String(255), primary_key=True)
    revision_id: Mapped[UUID]
    space_id: Mapped[UUID]
    indexed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
