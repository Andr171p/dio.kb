from pydantic import Field, PositiveInt
from pydantic_settings import BaseSettings, SettingsConfigDict


class KnowledgeGapsConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="GAPS_", frozen=True)

    min_signals: PositiveInt = Field(default=1, description="Минимум сигналов в группе для создания gap")
    batch_limit: PositiveInt = Field(default=200, le=2000)
    topic_hint_max_chars: PositiveInt = Field(default=120)
