from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class McpConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MCP_", url_preserve_empty_path=True)

    issuer_url: AnyHttpUrl = Field(  # type: ignore[assignment]
        default="https://iam.dios.cloud",
        description="URL издателя токенов DIOS",
    )
    resource_url: AnyHttpUrl = Field(
        default="https://kb.dios.cloud/api/mcp",
        description="Публичный URL MCP и audience токена",
    )


mcp_config = McpConfig()
