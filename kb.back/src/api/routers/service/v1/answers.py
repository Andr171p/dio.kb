"""Service API для AI Answers — те же use cases, что и user/v1."""

from src.api.routers.user.v1 import answers as user_answers

router = user_answers.router
