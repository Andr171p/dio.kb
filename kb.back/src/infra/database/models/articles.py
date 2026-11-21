from datetime import datetime
from uuid import UUID

from ddf.infra.database.sqlalchemy import Base, EntityMixin
from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column


class ArticleOrm(EntityMixin, Base):
    __tablename__ = "articles"

    organization_id: Mapped[UUID]
    space_id: Mapped[UUID] = mapped_column(ForeignKey("spaces.id"))
    slug: Mapped[str] = mapped_column(String(255))

    current_revision_id: Mapped[UUID] = mapped_column(
        ForeignKey("article_revisions.id", deferrable=True, initially="DEFERRED", use_alter=True),
    )
    published_revision_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("article_revisions.id", deferrable=True, initially="DEFERRED", use_alter=True),
    )
    revision_number: Mapped[int]

    author_id: Mapped[UUID]
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (UniqueConstraint("space_id", "slug", name="uq_articles_space_id_slug"),)


class ArticleRevisionOrm(EntityMixin, Base):
    __tablename__ = "article_revisions"

    article_id: Mapped[UUID] = mapped_column(
        ForeignKey("articles.id", deferrable=True, initially="DEFERRED"),
    )
    number: Mapped[int]
    previous_revision_id: Mapped[UUID | None]
    restored_from_revision_id: Mapped[UUID | None]

    title: Mapped[str] = mapped_column(String(255))
    summary: Mapped[str | None] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text)

    author_id: Mapped[UUID]
    change_note: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (UniqueConstraint("article_id", "number", name="uq_article_revisions_article_id_number"),)
