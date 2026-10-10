from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class SearchDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    query: str = Field(min_length=1, max_length=500, description="Поисковый запрос на естественном языке")
    space_ids: list[UUID] | None = Field(
        default=None, max_length=100, description="Искать только в пространствах"
    )
    limit: int = Field(default=10, ge=1, le=50, description="Максимальное количество статей")


class SearchFragmentResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    chunk_id: UUID = Field(description="Идентификатор фрагмента")
    text: str = Field(description="Фрагмент опубликованной редакции (Markdown)")
    heading_path: list[str] = Field(description="Путь заголовков до фрагмента")
    anchor: str | None = Field(description="Якорь раздела для прямой ссылки")
    score: float = Field(description="Релевантность фрагмента")


class SearchArticleResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    id: UUID = Field(description="Идентификатор статьи")
    space_id: UUID = Field(description="Пространство")
    slug: str = Field(description="Slug статьи")
    title: str = Field(description="Заголовок опубликованной редакции")
    revision_id: UUID = Field(description="Опубликованная редакция, к которой относятся фрагменты")
    published_at: AwareDatetime = Field(description="Дата публикации")


class SearchResultResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    article: SearchArticleResponse
    score: float = Field(description="Релевантность статьи")
    fragments: list[SearchFragmentResponse] = Field(description="Лучшие фрагменты статьи")


class SearchResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    items: list[SearchResultResponse] = Field(description="Найденные статьи по убыванию релевантности")


class SyncQueuedResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    queued: int = Field(description="Сколько статей поставлено на синхронизацию индекса")
