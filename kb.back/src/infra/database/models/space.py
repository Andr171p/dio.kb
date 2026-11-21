from uuid import UUID

from ddf.infra.database.sqlalchemy import Base, EntityMixin
from sqlalchemy import (
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column


class SpaceOrm(EntityMixin, Base):
    __tablename__ = "spaces"

    organization_id: Mapped[UUID]
    key: Mapped[str] = mapped_column(String(32))
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[UUID]

    __table_args__ = (UniqueConstraint("organization_id", "key", name="uq_spaces_organization_id_key"),)
