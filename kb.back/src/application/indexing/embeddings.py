from typing import Protocol

import math
from collections.abc import Awaitable, Callable, Collection, Mapping, Sequence
from dataclasses import replace
from itertools import batched

from .models import IndexedChunk

type EmbedDocuments = Callable[[Sequence[str]], Awaitable[Sequence[Sequence[float]]]]


class EmbeddingCache(Protocol):
    """Кеширование embedding-векторов (отдельный кеш от основной векторной БД).

     - ``version`` - идентифицирует embedding модель, её размерность и значимые параметры подготовки входа.
     - ``content_hash`` - вычисляется из ``search_text``.

    Важный момент: при изменении OCR модели меняется ``search_text`` -> изменится hash.

    Ключа кеша имеет вид: (embedding version, SHA256(search text))
    """

    async def get_many(self, content_hashes: Collection[str], version: str) -> dict[str, tuple[float, ...]]: ...

    async def put_many(self, embeddings: Mapping[str, tuple[float, ...]], version: str) -> None: ...


async def embed_chunks(
    chunks: Sequence[IndexedChunk],
    *,
    embed_documents: EmbedDocuments,
    cache: EmbeddingCache,
    version: str,
    batch_size: int = 32,
) -> list[IndexedChunk]:
    """Переиспользует embeddings по hash и версии модели."""

    if batch_size < 1:
        raise ValueError("batch_size must be positive")

    if not chunks:
        return []

    texts = {chunk.content_hash: chunk.search_text for chunk in chunks}

    vectors = await cache.get_many(texts.keys(), version)
    missing = [(key, text) for key, text in texts.items() if key not in vectors]

    for batch in batched(missing, batch_size, strict=False):
        embeddings = await embed_documents([text for _, text in batch])

        if len(embeddings) != len(batch):
            raise ValueError("Embedding provider returned an unexpected count")

        computed: dict[str, tuple[float, ...]] = {}

        for (key, _), embedding in zip(batch, embeddings, strict=True):
            vector = tuple(embedding)

            if not vector or not all(math.isfinite(value) for value in vector):
                raise ValueError("Invalid embedding vector")

            computed[key] = vector

        await cache.put_many(computed, version)
        vectors.update(computed)

    return [replace(chunk, embedding=vectors[chunk.content_hash]) for chunk in chunks]


__all__ = ["EmbedDocuments", "EmbeddingCache", "embed_chunks"]
