from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, PositiveInt
from pydantic.alias_generators import to_camel

from src.domain.articles.types import ArticleStatus

SLUG_PATTERN = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"


class CreateArticleDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    slug: str = Field(
        max_length=255, pattern=SLUG_PATTERN, description="Человекочитаемый идентификатор для URL"
    )
    title: str = Field(min_length=1, max_length=255, description="Заголовок")
    content: str = Field(min_length=1, description="Содержимое статьи в формате Markdown")
    summary: str | None = Field(default=None, min_length=1, description="Краткое содержание")


class ReviseArticleDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    expected_revision_id: UUID = Field(description="Редакция, на основе которой сделаны изменения")
    title: str = Field(min_length=1, max_length=255, description="Заголовок")
    content: str = Field(min_length=1, description="Содержание статьи в формате Markdown")
    summary: str | None = Field(default=None, min_length=1, description="Краткое содержание")
    change_note: str | None = Field(default=None, min_length=1, description="Что изменено")


class RestoreArticleRevisionDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    expected_revision_id: UUID = Field(description="Текущая редакция, которую видел редактор")
    change_note: str | None = Field(default=None, min_length=1, description="Комментарий к восстановлению")


class PublishArticleDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    revision_id: UUID = Field(description="Публикуемая редакция (должна быть текущей)")


class ArticleResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, from_attributes=True)

    id: UUID = Field(description="Уникальный идентификатор статьи")
    created_at: AwareDatetime = Field(description="Дата создания")
    updated_at: AwareDatetime = Field(description="Дата последнего обновления")

    space_id: UUID = Field(description="Идентификатор пространства")
    slug: str = Field(description="Уникальный строковый идентификатор в рамках пространства")
    status: ArticleStatus = Field(description="Текущий статус")

    current_revision_id: UUID = Field(description="Идентификатор текущей (редакторской) редакции")
    published_revision_id: UUID | None = Field(description="Идентификатор опубликованной редакции")
    revision_number: PositiveInt = Field(description="Номер текущей редакции")
    has_unpublished_changes: bool = Field(description="Есть ли неопубликованные изменения")

    author_id: UUID = Field(description="Автор статьи")
    published_at: AwareDatetime | None = Field(description="Дата публикации")


class ArticleRevisionSummaryResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, from_attributes=True)

    id: UUID = Field(description="Уникальный идентификатор редакции")
    created_at: AwareDatetime = Field(description="Дата создания")
    number: PositiveInt = Field(description="Порядковый номер")
    title: str = Field(description="Заголовок")
    author_id: UUID = Field(description="Автор редакции")
    change_note: str | None = Field(description="Что было изменено")
    restored_from_revision_id: UUID | None = Field(description="Редакция, из которой восстановлена")


class ArticleRevisionResponse(ArticleRevisionSummaryResponse):
    article_id: UUID = Field(description="Статья, которой принадлежит редакция")
    previous_revision_id: UUID | None = Field(description="Предыдущая редакция")
    summary: str | None = Field(description="Краткое содержание")
    content: str = Field(description="Контент в формате Markdown")


class ArticleDetailResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    article: ArticleResponse
    revision: ArticleRevisionResponse


class ArticleSummaryResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, from_attributes=True)

    id: UUID = Field(description="Идентификатор статьи")
    space_id: UUID = Field(description="Пространство")
    slug: str = Field(description="Slug статьи")
    title: str = Field(description="Заголовок")
    status: ArticleStatus = Field(description="Статус")
    updated_at: AwareDatetime = Field(description="Дата последнего обновления")
    published_at: AwareDatetime | None = Field(description="Дата публикации")
