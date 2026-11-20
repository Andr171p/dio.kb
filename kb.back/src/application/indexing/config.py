from pydantic import Field, PositiveFloat, PositiveInt
from pydantic_settings import BaseSettings, SettingsConfigDict


class ImageProcessingConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="IMAGE_PROCESSING_")

    max_bytes: PositiveInt = Field(
        default=12 * 1024 * 1024,
        description="Максимальный размер исходного изображения в байтах",
    )
    max_pixels: PositiveInt = Field(
        default=32_000_000,
        description="Максимальное количество пикселей после декодирования изображения",
    )

    max_concurrent_analyses: PositiveInt = Field(
        default=4,
        description="Максимум параллельных vision-запросов при обработке одной статьи",
    )
    analysis_timeout: PositiveFloat = Field(default=60.0, description="Таймаут одного анализа изображения в секундах")
    analysis_version: str | None = Field(
        default=None,
        description="Версия полного алгоритма анализа: модель, промпт и preprocessing",
        examples=["vision-v2-prompt-v3"],
    )


class MarkdownChunkingConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MARKDOWN_CHUNKING_")

    target_chars: int = Field(default=1600, ge=256, le=16000, description="Целевой размер Markdown фрагмента")


class IndexingConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="INDEXING_")

    embedding_batch_size: PositiveInt = Field(
        default=32,
        description="Максимальное количество текстов в одном запросе к embedding-провайдеру",
    )
    index_write_batch_size: PositiveInt = Field(
        default=100,
        description="Максимальное количество индексных документов в одной операции записи",
    )
