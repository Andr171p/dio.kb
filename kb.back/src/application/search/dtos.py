from typing import Annotated

from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, PositiveInt, StringConstraints
from pydantic.alias_generators import to_camel

SearchText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]

SuggestionText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=100)]


class _CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        validate_by_name=True,
        serialize_by_alias=True,
        extra="forbid",
    )


class SuggestionRequest(_CamelModel):
    query: SuggestionText
    space_ids: list[UUID] | None = Field(default=None, max_length=100)
    limit: PositiveInt = Field(default=6, le=10)


class SearchRequest(_CamelModel):
    query: SearchText = Field(description="Поисковый запрос")
    space_ids: list[UUID] | None = Field(
        default=None,
        max_length=100,
        description="Ограничение поиска выбранными пространствами",
    )
    limit: PositiveInt = Field(default=10, le=50, description="Максимальное количество статей в ответе")


class SearchFragment(_CamelModel):
    chunk_id: UUID = Field(description="Идентификатор фрагмента")
    text: str = Field(description="Фрагмент опубликованной редакции (Markdown)")
    heading_path: list[str] = Field(description="Путь заголовков до фрагмента")
    anchor: str | None = Field(description="Якорь раздела для прямой ссылки")
    score: float = Field(description="Релевантность фрагмента")


class SearchArticle(_CamelModel):
    id: UUID
    space_id: UUID
    slug: str
    title: str
    revision_id: UUID
    published_at: AwareDatetime


class SearchResult(_CamelModel):
    article: SearchArticle
    score: float
    fragments: list[SearchFragment]


class SearchResponse(_CamelModel):
    items: list[SearchResult] = Field(description="Найденные статьи по убыванию релевантности")


class SuggestionResult(_CamelModel):
    article_id: UUID
    space_id: UUID
    slug: str
    title: str


class SuggestionsResponse(_CamelModel):
    items: list[SuggestionResult] = Field(description="Найденные подсказки по убыванию релевантности")
