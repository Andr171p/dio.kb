from typing import Annotated

from fastapi import Depends

from src.api.dependencies.db import DBSession
from src.application.search.indexes import SuggestionIndex
from src.infra.aitunnel import AiTunnelConfig, AiTunnelTextEmbedder
from src.infra.database.repositories.suggestions import SqlAlchemySuggestionIndex
from src.infra.qdrant import QdrantConfig, QdrantSearchIndex

aitunnel_config = AiTunnelConfig()  # type: ignore[call-arg]
text_embedder = aitunnel_text_embedder = AiTunnelTextEmbedder(aitunnel_config)

qdrant_config = QdrantConfig()
search_index = qdrant_search_index = QdrantSearchIndex(qdrant_config)


def get_suggestion_index(session: DBSession) -> SuggestionIndex:
    return SqlAlchemySuggestionIndex(session)


SuggestionIndexDep = Annotated[SuggestionIndex, Depends(get_suggestion_index)]
