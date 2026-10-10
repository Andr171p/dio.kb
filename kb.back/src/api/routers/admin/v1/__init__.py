from fastapi import APIRouter

from . import access, search, spaces

router = APIRouter(prefix="/v1")
__all__ = ["router"]

router.include_router(spaces.router)
router.include_router(access.router)
router.include_router(search.router)
