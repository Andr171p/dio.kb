from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class RedisConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="REDIS_", frozen=True)

    host: str = Field(default="localhost")
    port: int = Field(default=6379, ge=1, le=65535)
    db: int = Field(default=0, ge=0)
    password: SecretStr | None = Field(default=None)

    @property
    def url(self) -> str:
        password = self.password.get_secret_value() if self.password else ""
        auth = f":{password}@" if password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"
