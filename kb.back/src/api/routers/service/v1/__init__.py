from fastapi import APIRouter, Depends

from src.api.dependencies.auth import get_current_service

from . import articles, collections, links, search, spaces

router = APIRouter(prefix="/v1", dependencies=[Depends(get_current_service)])

router.include_router(spaces.router)
router.include_router(collections.router)
router.include_router(articles.router)
router.include_router(search.router)
router.include_router(links.router)
