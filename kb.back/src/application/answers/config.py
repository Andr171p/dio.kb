from enum import StrEnum

from pydantic import Field, PositiveInt
from pydantic_settings import BaseSettings, SettingsConfigDict


class AnswersPrivacyMode(StrEnum):
    FULL = "full"
    METADATA_ONLY = "metadata_only"


class AnswersProgressBackend(StrEnum):
    MEMORY = "memory"
    REDIS = "redis"


class AnswersConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ANSWERS_", frozen=True)

    privacy_mode: AnswersPrivacyMode = AnswersPrivacyMode.FULL
    progress_backend: AnswersProgressBackend = AnswersProgressBackend.REDIS
    public_base_url: str = Field(default="", description="Опциональный origin для абсолютных URL источников")

    candidates_limit: PositiveInt = Field(default=8, le=50)
    max_sources: PositiveInt = Field(default=8, le=50)
    max_excerpt_chars: PositiveInt = Field(default=2000)
    max_output_tokens: PositiveInt = Field(default=800)
    retrieval_timeout: float = Field(default=10.0, gt=0)
    generation_timeout: float = Field(default=60.0, gt=0)
    total_timeout: float = Field(default=90.0, gt=0)
    progress_heartbeat_seconds: float = Field(default=12.0, gt=0)
    lease_seconds: PositiveInt = Field(default=120)
    prompt_version: str = Field(default="answers-v1")
    retrieval_version: str = Field(default="hybrid-v1")
