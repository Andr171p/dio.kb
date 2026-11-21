from pydantic import Field, PositiveInt
from pydantic_settings import BaseSettings, SettingsConfigDict


class SearchConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SEARCH_")

    hits_per_article: PositiveInt = Field(default=3, le=10, description="Размер выдачи внутри группы")
    candidate_multiplier: PositiveInt = Field(default=5, le=20)
    max_candidates: int = Field(default=250, ge=50, le=2000, description="Количество групп-статей")

    suggestions_limit: PositiveInt = Field(default=8, le=20)
    suggestion_candidate_multiplier: PositiveInt = Field(default=4, le=20)
