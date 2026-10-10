from openai import AsyncOpenAI

from .config import AiTunnelConfig
from .embedder import OpenAITextEmbedder
from .image_extractor import OpenAIImageTextExtractor


def create_openai_client(config: AiTunnelConfig) -> AsyncOpenAI:
    return AsyncOpenAI(
        api_key=config.api_key.get_secret_value(),
        base_url=str(config.base_url),
        timeout=config.timeout,
        max_retries=config.max_retries,
    )


__all__ = ["AiTunnelConfig", "OpenAIImageTextExtractor", "OpenAITextEmbedder", "create_openai_client"]
