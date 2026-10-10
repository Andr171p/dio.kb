from fastapi import APIRouter

from . import articles, collections, links, search, spaces

router = APIRouter(prefix="/v1")
__all__ = ["router"]

router.include_router(spaces.router)
router.include_router(collections.router)
router.include_router(articles.router)
router.include_router(search.router)
router.include_router(links.router)
