from collections.abc import Sequence

from openai import AsyncOpenAI


class OpenAITextEmbedder:
    def __init__(self, client: AsyncOpenAI, *, model: str, dimensions: int, batch_size: int = 64) -> None:
        self._client = client
        self._model = model
        self._dimensions = dimensions
        self._batch_size = batch_size

    @property
    def model(self) -> str:
        return self._model

    @property
    def dimensions(self) -> int:
        return self._dimensions

    async def embed_documents(self, texts: Sequence[str]) -> list[tuple[float, ...]]:
        vectors: list[tuple[float, ...]] = []

        for start in range(0, len(texts), self._batch_size):
            response = await self._client.embeddings.create(
                model=self._model,
                input=list(texts[start : start + self._batch_size]),
                dimensions=self._dimensions,
            )
            vectors.extend(
                tuple(item.embedding) for item in sorted(response.data, key=lambda item: item.index)
            )

        return vectors

    async def embed_query(self, text: str) -> tuple[float, ...]:
        [vector] = await self.embed_documents([text])
        return vector
