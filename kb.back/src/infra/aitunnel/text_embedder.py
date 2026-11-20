from collections.abc import Sequence
from itertools import batched

from openai import AsyncOpenAI

from .config import AiTunnelConfig


class AiTunnelTextEmbedder:
    def __init__(self, config: AiTunnelConfig) -> None:
        self._config = config
        self._client = AsyncOpenAI(
            api_key=config.api_key.get_secret_value(),
            base_url=str(config.base_url),
            timeout=float(config.timeout),
            max_retries=config.max_retries,
        )

    @property
    def model(self) -> str:
        return self._config.embedding_model

    @property
    def dimensions(self) -> int:
        return self._config.embedding_dimensions

    async def embed_documents(self, texts: Sequence[str]) -> list[tuple[float, ...]]:
        if not texts:
            return []

        vectors: list[tuple[float, ...]] = []

        for batch in batched(texts, self._config.embedding_batch_size, strict=False):
            response = await self._client.embeddings.create(
                model=self._config.embedding_model,
                input=list(batch),
                dimensions=self._config.embedding_dimensions,
            )
            vectors.extend(tuple(item.embedding) for item in sorted(response.data, key=lambda item: item.index))

        return vectors

    async def embed_query(self, text: str) -> tuple[float, ...]:
        [vector] = await self.embed_documents([text])
        return vector

    async def close(self) -> None:
        await self._client.close()
