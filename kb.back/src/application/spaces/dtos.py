from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from src.application.access.dtos import PermissionDTO

SPACE_KEY_PATTERN = r"^[A-Z][A-Z0-9_]{1,31}$"


class CreateSpaceDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    key: str = Field(pattern=SPACE_KEY_PATTERN, description="Короткий ключ пространства", examples=["ITSM"])
    name: str = Field(min_length=1, max_length=255, description="Название")
    description: str | None = Field(default=None, min_length=1, description="Описание")
    organization_wide: bool = Field(
        default=False,
        description="Выдать READ всей организации (иначе доступ только по явным grants)",
    )


class UpdateSpaceDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    name: str | None = Field(default=None, min_length=1, max_length=255, description="Название")
    description: str | None = Field(default=None, description="Описание (пустая строка очищает)")


class SpaceResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, from_attributes=True)

    id: UUID = Field(description="Уникальный идентификатор пространства")
    created_at: AwareDatetime = Field(description="Дата создания")
    updated_at: AwareDatetime = Field(description="Дата последнего обновления")

    key: str = Field(description="Короткий ключ пространства")
    name: str = Field(description="Название")
    description: str | None = Field(description="Описание")
    created_by: UUID = Field(description="Создатель")
    permissions: PermissionDTO = Field(description="Эффективные права пользователя на пространство")
