from fastapi import APIRouter

from . import admin, user

router = APIRouter()
__all__ = ["router"]

router.include_router(admin.router)
router.include_router(user.router)
