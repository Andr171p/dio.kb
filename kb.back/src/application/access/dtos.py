from typing import Annotated, Literal

from uuid import UUID

from pydantic import AwareDatetime, BaseModel, BeforeValidator, ConfigDict, Field, PlainSerializer
from pydantic.alias_generators import to_camel

from src.domain.access.types import Permission
from src.domain.access.vo import Resource, Subject

type ResourceType = Literal["space", "collection", "article"]
type SubjectType = Literal["organization", "user", "role"]


def _parse_permission(value: object) -> Permission:
    if isinstance(value, Permission):
        return value

    if isinstance(value, int):
        return Permission(value)

    if isinstance(value, str):
        value = [value]

    if isinstance(value, list):
        result = Permission(0)
        for name in value:
            try:
                result |= Permission[str(name).upper().strip()]
            except KeyError as exc:
                raise ValueError(f"Unknown permission flag name: {name}") from exc
        return result

    raise ValueError("Expected a string, a list of strings, or a number.")


def _serialize_permission(permission: Permission) -> list[str]:
    return [flag.name for flag in Permission if flag in permission and flag.name]


PermissionDTO = Annotated[
    Permission,
    BeforeValidator(_parse_permission),
    PlainSerializer(_serialize_permission, return_type=list[str]),
    Field(json_schema_extra={"type": "array", "items": {"enum": [flag.name for flag in Permission]}}),
]


class ResourceDTO(BaseModel):
    type: ResourceType = Field(description="Тип ресурса")
    id: UUID = Field(description="Идентификатор ресурса")


class SubjectDTO(BaseModel):
    type: SubjectType = Field(description="Тип субъекта")
    id: str = Field(min_length=1, max_length=255, description="ID пользователя, код роли или ID организации")


class CreateAccessGrantDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    resource: ResourceDTO = Field(description="Ресурс, на который выдаётся право")
    subject: SubjectDTO = Field(description="Субъект, которому выдаётся право")
    permissions: PermissionDTO = Field(description="Права, которые будут назначены")


class UpdateAccessGrantDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    permissions: PermissionDTO = Field(description="Новые права")


class AccessGrantResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, from_attributes=True)

    id: UUID = Field(description="Уникальный идентификатор предоставленного доступа")
    created_at: AwareDatetime = Field(description="Дата выдачи")
    granted_by: UUID = Field(description="Кто выдал доступ")
    resource: Resource = Field(description="Ресурс, к которому предоставлен доступ")
    subject: Subject = Field(description="Субъект, которому предоставили доступ")
    permissions: PermissionDTO = Field(description="Права, которые выданы субъекту")
