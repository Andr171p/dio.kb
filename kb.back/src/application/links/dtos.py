from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class LinkPreviewResponse(BaseModel):
    """Метаданные страницы (OpenGraph / HTML). Пустые поля — страница недоступна или без разметки."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    url: str = Field(description="Итоговый адрес страницы после редиректов")
    title: str | None = Field(default=None, description="Заголовок")
    description: str | None = Field(default=None, description="Описание")
    image_url: str | None = Field(default=None, description="Изображение превью")
    site_name: str | None = Field(default=None, description="Название сайта")
    favicon_url: str | None = Field(default=None, description="Иконка сайта")
