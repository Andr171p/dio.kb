from pydantic import Field, HttpUrl, PositiveInt, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class AiTunnelConfig(BaseSettings):
    """OpenAI-совместимый провайдер AI Tunnel."""

    model_config = SettingsConfigDict(env_prefix="AITUNNEL_")

    api_key: SecretStr = Field(description="API ключ AI Tunnel")
    base_url: HttpUrl = Field(default=HttpUrl("https://api.aitunnel.ru/v1"), description="Базовый URL API")
    timeout: PositiveInt = Field(default=60, description="Таймаут запроса в секундах")
    max_retries: int = Field(default=3, ge=0, description="Повторы при сетевых ошибках и 429/5xx")

    embedding_model: str = Field(default="text-embedding-3-small", description="Модель эмбеддингов")
    embedding_dimensions: PositiveInt = Field(default=512, description="Размерность эмбеддингов")
    embedding_batch_size: PositiveInt = Field(default=64, description="Текстов в одном запросе эмбеддингов")

    vision_model: str = Field(
        default="gpt-4.1-nano", description="Vision-модель для OCR и описания изображений"
    )
