from uuid import UUID

from ddf.infra.database.sqlalchemy import Base, EntityMixin
from sqlalchemy import (
    Index,
    Integer,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column


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
