from pydantic import BaseModel, ConfigDict, Field, HttpUrl
from pydantic.alias_generators import to_camel


class LinkPreview(BaseModel):
    """Метаданные страницы (OpenGraph / HTML). Пустые поля — страница недоступна или без разметки."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    url: HttpUrl = Field(description="Итоговый адрес страницы после редиректов")
    title: str | None = None
    description: str | None = None
    image_url: str | None = None
    site_name: str | None = None
    favicon_url: str | None = None
