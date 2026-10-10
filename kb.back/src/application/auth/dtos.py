from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

# ЗАГЛУШКА для Legacy IAM (текущая реализация не поддерживает multi-tenancy)
_STUB_ORGANIZATION_ID = UUID("00000000-0000-0000-0000-000000000000")

ADMIN_ROLE = "admin"


class AuthType(StrEnum):
    """Тип аутентифицированного субъекта (роль — отдельное понятие, см. ``roles``)."""

    USER = "user"
    SERVICE = "service"


class Auth(BaseModel):
    model_config = ConfigDict(frozen=True)

    class User(BaseModel):
        model_config = ConfigDict(frozen=True)

        id: UUID
        email: EmailStr
        organization_id: UUID = _STUB_ORGANIZATION_ID
        roles: frozenset[str] = Field(default_factory=frozenset)

    id: UUID
    type: AuthType

    user: User | None = None


class AuthUser(Auth):
    """Аутентифицированный пользователь."""

    user: Auth.User

    @property
    def is_admin(self) -> bool:
        return ADMIN_ROLE in self.user.roles
