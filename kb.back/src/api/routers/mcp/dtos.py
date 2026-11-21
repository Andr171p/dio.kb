from uuid import UUID

from pydantic import BaseModel, Field


class KnowledgeMatch(BaseModel):
    article_id: UUID = Field(description="UUID для вызова get_article.")
    title: str
    url: str = Field(description="Ссылка на опубликованную статью.")
    fragments: list[str] = Field(description="Релевантные фрагменты опубликованной редакции в Markdown.")


class KnowledgeSearchResult(BaseModel):
    items: list[KnowledgeMatch] = Field(description="Статьи в порядке убывания релевантности.")


class KnowledgeArticle(BaseModel):
    article_id: UUID
    title: str
    url: str = Field(description="Ссылка на опубликованную статью.")
    markdown: str = Field(description="Текст опубликованной редакции в Markdown.")
    truncated: bool = Field(default=False, description="Признак сокращения текста.")


class KnowledgeSpace(BaseModel):
    id: UUID = Field(description="UUID для фильтра space_ids в search_knowledge.")
    name: str


class KnowledgeSpacesResult(BaseModel):
    items: list[KnowledgeSpace] = Field(description="Пространства, доступные пользователю на чтение.")
