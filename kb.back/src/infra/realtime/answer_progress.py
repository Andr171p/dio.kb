"""Progress notifications: PostgreSQL snapshot + memory/Redis pub-sub."""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from collections.abc import AsyncIterator, Callable
from uuid import UUID

from redis.asyncio import Redis

from src.application.answers.config import AnswersProgressBackend

logger = logging.getLogger(__name__)

CHANNEL_PREFIX = "answer:"


class MemoryAnswerProgressNotifier:
    def __init__(self) -> None:
        self._waiters: dict[UUID, list[asyncio.Event]] = defaultdict(list)

    async def notify(self, run_id: UUID) -> None:
        for event in list(self._waiters.get(run_id, [])):
            event.set()

    async def subscribe(self, run_id: UUID) -> AsyncIterator[None]:
        event = asyncio.Event()
        self._waiters[run_id].append(event)
        try:
            while True:
                await event.wait()
                event.clear()
                yield None
        finally:
            waiters = self._waiters.get(run_id, [])
            if event in waiters:
                waiters.remove(event)
            if not waiters:
                self._waiters.pop(run_id, None)


class RedisAnswerProgressNotifier:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def notify(self, run_id: UUID) -> None:
        try:
            await self._redis.publish(f"{CHANNEL_PREFIX}{run_id}", "1")
        except Exception:
            logger.warning("Failed to publish answer progress for %s", run_id, exc_info=True)

    async def subscribe(self, run_id: UUID) -> AsyncIterator[None]:
        pubsub = self._redis.pubsub()
        channel = f"{CHANNEL_PREFIX}{run_id}"
        await pubsub.subscribe(channel)
        try:
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message is not None:
                    yield None
                else:
                    await asyncio.sleep(0)
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.aclose()


type AnswerProgressNotifier = MemoryAnswerProgressNotifier | RedisAnswerProgressNotifier


def create_answer_progress_notifier(
    backend: AnswersProgressBackend,
    *,
    redis_factory: Callable[[], Redis] | None = None,
) -> AnswerProgressNotifier:
    if backend is AnswersProgressBackend.MEMORY:
        return MemoryAnswerProgressNotifier()
    if redis_factory is None:
        raise ValueError("redis_factory is required for redis progress backend")
    return RedisAnswerProgressNotifier(redis_factory())
