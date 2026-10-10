from ddf.application.repositories import Repository

from src.domain.spaces.models import Space

type SpaceRepository = Repository[Space]

__all__ = ["SpaceRepository"]
