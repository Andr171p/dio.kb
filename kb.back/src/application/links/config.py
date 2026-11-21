from pydantic import Field, PositiveFloat, PositiveInt
from pydantic_settings import BaseSettings, SettingsConfigDict


class LinkPreviewConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LINK_PREVIEW_")

    timeout_seconds: PositiveFloat = Field(
        default=5.0,
        description="Максимальное время HTTP-запроса в секундах",
    )
    max_redirects: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Максимальное число перенаправлений",
    )
    max_body_bytes: PositiveInt = Field(
        default=512 * 1024,
        description="Максимум HTML-байтов для разбора метаданных",
    )
    max_url_chars: PositiveInt = Field(default=2048, description="Максимальная длина запрашиваемого URL")
    max_text_chars: PositiveInt = Field(default=300, description="Максимальная длина текстовых полей превью")
    max_connections: PositiveInt = Field(default=20, description="Максимум HTTP-соединений одного процесса")
    max_concurrent_fetches: PositiveInt = Field(default=10, description="Максимум одновременных загрузок страниц")
    cache_ttl_seconds: PositiveInt = Field(default=3600, description="TTL успешно полученных метаданных")
    failure_cache_ttl_seconds: PositiveInt = Field(default=300, description="TTL временно недоступных страниц")
