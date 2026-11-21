from fastapi import APIRouter

from . import admin, service, user

router = APIRouter()
__all__ = ["router"]

router.include_router(admin.router)
router.include_router(user.router)

router.include_router(service.router)
