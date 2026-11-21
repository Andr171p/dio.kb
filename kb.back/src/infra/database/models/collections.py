from uuid import UUID

from ddf.infra.database.sqlalchemy import Base, EntityMixin
from sqlalchemy import (
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column


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
