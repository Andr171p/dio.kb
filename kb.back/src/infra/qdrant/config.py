from pydantic import Field, HttpUrl, PositiveInt, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class QdrantConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="QDRANT_")

    url: HttpUrl = Field(default=HttpUrl("http://localhost:6333"), description="URL Qdrant (HTTP API)")
    api_key: SecretStr | None = Field(default=None, description="API ключ Qdrant")
    timeout: PositiveInt = Field(default=30, description="Таймаут запросов в секундах")

    collection: str = Field(default="kb_chunks", description="Базовое имя коллекции фрагментов")
    generation: PositiveInt = Field(
        default=1,
        description="Поколение индекса: увеличивается при смене embedding-модели, размерности или парсера",
    )
    bm25_language: str = Field(default="russian", description="Язык стемминга и стоп-слов серверного BM25")

    @property
    def collection_name(self) -> str:
        return f"{self.collection}_g{self.generation}"
