from typing import Annotated, Literal

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class IndexArticle(BaseModel):
    """Подходит и для первичной индексации, и для повторной — worker должен получить
    актуальную опубликованную редакцию из БД."""

    model_config = ConfigDict(frozen=True)

    type: Literal["index_article"] = "index_article"

    organization_id: UUID
    article_id: UUID
    force: bool = False


class ReconcileIndex(BaseModel):
    model_config = ConfigDict(frozen=True)

    type: Literal["reconcile_index"] = "reconcile_index"

    organization_id: UUID
    generation: str
    mode: Literal["stale", "rebuild"] = Field(
        default="stale",
        description=(
            "`stale` - статьи, отсутствующие в актуальной проекции либо имеющие несовпадающий checkpoint."
            "`rebuild` - все статьи, которые должны быть в индексе, независимо от checkpoint."
        ),
    )


IndexCommand = Annotated[IndexArticle | ReconcileIndex, Field(discriminator="type")]
