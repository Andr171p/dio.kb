from qdrant_client import AsyncQdrantClient

from .config import QdrantConfig
from .repository import QdrantSearchChunkRepository


def create_qdrant_client(config: QdrantConfig) -> AsyncQdrantClient:
    # cloud_inference: Document (BM25) отправляется на сервер Qdrant, а не считается локально через fastembed
    return AsyncQdrantClient(
        url=str(config.url),
        api_key=config.api_key.get_secret_value() if config.api_key else None,
        timeout=config.timeout,
        cloud_inference=True,
    )


__all__ = ["QdrantConfig", "QdrantSearchChunkRepository", "create_qdrant_client"]
