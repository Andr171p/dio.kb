from typing import Self

from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel

from src.application.articles.dtos import SLUG_PATTERN
from src.domain.articles.types import ArticleStatus
from src.domain.collections.vo import CollectionTarget, TargetType


class RelativePosition(BaseModel):
    """Позиция относительно соседнего размещения; без соседей — в конец коллекции."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    before_id: UUID | None = Field(default=None, description="Разместить перед этим размещением")
    after_id: UUID | None = Field(default=None, description="Разместить после этого размещения")

    @model_validator(mode="after")
    def _single_anchor(self) -> Self:
        if self.before_id is not None and self.after_id is not None:
            raise ValueError("Only one of beforeId or afterId can be provided.")
        return self


class CreateCollectionDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    name: str = Field(min_length=1, max_length=255, description="Имя коллекции")
    slug: str = Field(max_length=255, pattern=SLUG_PATTERN, description="Человекочитаемый фрагмент для URL")
    description: str | None = Field(default=None, min_length=1, description="Описание")
    parent_id: UUID | None = Field(
        default=None, description="Родительская коллекция (элемент встанет в конец)"
    )


class UpdateCollectionDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    name: str | None = Field(default=None, min_length=1, max_length=255, description="Имя коллекции")
    slug: str | None = Field(
        default=None, max_length=255, pattern=SLUG_PATTERN, description="Фрагмент для URL"
    )
    description: str | None = Field(default=None, description="Описание (пустая строка очищает)")


class CollectionResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, from_attributes=True)

    id: UUID = Field(description="Уникальный идентификатор коллекции")
    created_at: AwareDatetime = Field(description="Дата создания")
    updated_at: AwareDatetime = Field(description="Дата последнего обновления")

    space_id: UUID = Field(description="Пространство, в котором находится коллекция")
    name: str = Field(description="Имя коллекции")
    slug: str = Field(description="Человекочитаемый фрагмент для URL")
    description: str | None = Field(description="Описание")


class CreatePlacementDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    target: CollectionTarget = Field(description="Размещаемый элемент")
    position: RelativePosition = Field(default_factory=RelativePosition, description="Позиция")


class MovePlacementDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    collection_id: UUID | None = Field(default=None, description="Новая коллекция (по умолчанию — текущая)")
    position: RelativePosition = Field(default_factory=RelativePosition, description="Позиция")


class CollectionPlacementResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, from_attributes=True)

    id: UUID = Field(description="Уникальный идентификатор размещения")
    collection_id: UUID = Field(description="Коллекция, в которой размещён элемент")
    target: CollectionTarget = Field(description="Размещённый элемент")
    rank: str = Field(description="Ранг для сортировки (сравнение побайтно)")


class NavigationNode(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    type: TargetType = Field(description="Тип узла")
    id: UUID = Field(description="Идентификатор коллекции или статьи")
    placement_id: UUID | None = Field(default=None, description="Размещение узла (для перемещения)")
    title: str = Field(description="Название коллекции или заголовок статьи")
    slug: str = Field(description="Slug")
    status: ArticleStatus | None = Field(default=None, description="Статус статьи")
    children: list[NavigationNode] = Field(default_factory=list, description="Дочерние элементы")


class SpaceNavigationResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    collections: list[NavigationNode] = Field(description="Корневые коллекции с вложенными элементами")
    unplaced_articles: list[NavigationNode] = Field(description="Статьи вне коллекций")
