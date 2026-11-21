"""Service API для Knowledge Gaps — те же use cases, что и user/v1."""

from src.api.routers.user.v1 import knowledge_gaps as user_gaps

router = user_gaps.router
