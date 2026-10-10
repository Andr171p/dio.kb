from fastapi import APIRouter

from . import v1

router = APIRouter(prefix="/user")
__all__ = ["router"]

router.include_router(v1.router)
