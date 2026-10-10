from datetime import datetime
from uuid import UUID

from ddf.infra.database.sqlalchemy import Base, EntityMixin
from ddf.infra.outbox.sqlalchemy import OutboxMessageOrm
from sqlalchemy import (
    ARRAY,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column


class SpaceOrm(EntityMixin, Base):
    __tablename__ = "spaces"

    organization_id: Mapped[UUID]
    key: Mapped[str] = mapped_column(String(32))
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[UUID]

    __table_args__ = (UniqueConstraint("organization_id", "key", name="uq_spaces_organization_id_key"),)


class CollectionOrm(EntityMixin, Base):
    __tablename__ = "collections"

    organization_id: Mapped[UUID]
    space_id: Mapped[UUID] = mapped_column(ForeignKey("spaces.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        Index(
            "uq_collections_space_id_slug",
            "space_id",
            "slug",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )


class CollectionPlacementOrm(EntityMixin, Base):
    __tablename__ = "collection_placements"

    collection_id: Mapped[UUID] = mapped_column(ForeignKey("collections.id", ondelete="CASCADE"))
    target_type: Mapped[str] = mapped_column(String(16))
    target_id: Mapped[UUID]
    # Побайтное сравнение: ранги base62 упорядочиваются корректно только в collation "C"
    rank: Mapped[str] = mapped_column(String(128, collation="C"))

    __table_args__ = (
        UniqueConstraint(
            "collection_id",
            "target_type",
            "target_id",
            name="uq_collection_placements_collection_target",
        ),
        # У коллекции может быть только один родитель
        Index(
            "uq_collection_placements_single_parent",
            "target_id",
            unique=True,
            postgresql_where=text("target_type = 'collection'"),
        ),
        Index("ix_collection_placements_collection_id_rank", "collection_id", "rank"),
        Index("ix_collection_placements_target", "target_type", "target_id"),
    )


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

    __table_args__ = (
        UniqueConstraint("article_id", "number", name="uq_article_revisions_article_id_number"),
    )


class AccessGrantOrm(EntityMixin, Base):
    __tablename__ = "access_grants"

    organization_id: Mapped[UUID]
    granted_by: Mapped[UUID]
    resource_type: Mapped[str] = mapped_column(String(32))
    resource_id: Mapped[UUID]
    subject_type: Mapped[str] = mapped_column(String(32))
    subject_id: Mapped[str] = mapped_column(String(255))
    permissions: Mapped[int] = mapped_column(Integer)

    __table_args__ = (
        Index(
            "uq_access_grants_active",
            "organization_id",
            "resource_type",
            "resource_id",
            "subject_type",
            "subject_id",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index(
            "ix_access_grants_subject",
            "organization_id",
            "subject_type",
            "subject_id",
            "resource_type",
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )


class ImageTextOrm(Base):
    __tablename__ = "image_texts"

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


__all__ = [
    "AccessGrantOrm",
    "ArticleIndexStateOrm",
    "ArticleOrm",
    "ArticleRevisionOrm",
    "Base",
    "CollectionOrm",
    "CollectionPlacementOrm",
    "ImageTextOrm",
    "OutboxMessageOrm",
    "SpaceOrm",
]
