from fastapi import APIRouter, Depends

from src.api.dependencies.auth import get_current_client

from . import answers, articles, collections, knowledge_gaps, links, search, spaces

router = APIRouter(prefix="/v1", dependencies=[Depends(get_current_client)])

router.include_router(spaces.router)
router.include_router(collections.router)
router.include_router(articles.router)
router.include_router(search.router)
router.include_router(links.router)
router.include_router(answers.router)
router.include_router(knowledge_gaps.router)
