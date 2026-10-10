from typing import Annotated

from fastapi import Depends, Request

from src.application.search.protocols import IndexingQueue, TextEmbedder
from src.application.search.repositories import SearchChunkRepository


def get_chunk_repository(request: Request) -> SearchChunkRepository:
    return request.app.state.chunk_repository


def get_embedder(request: Request) -> TextEmbedder:
    return request.app.state.embedder


def get_indexing_queue(request: Request) -> IndexingQueue:
    return request.app.state.indexing_queue


ChunkRepositoryDep = Annotated[SearchChunkRepository, Depends(get_chunk_repository)]
EmbedderDep = Annotated[TextEmbedder, Depends(get_embedder)]
IndexingQueueDep = Annotated[IndexingQueue, Depends(get_indexing_queue)]
