"""Taskiq-брокер (RabbitMQ): общий для отправки задач (API, relay) и их выполнения (worker)."""

from dotenv import load_dotenv
from taskiq.middlewares import SmartRetryMiddleware
from taskiq_aio_pika import AioPikaBroker

from .config import RabbitConfig

load_dotenv()

broker = AioPikaBroker(RabbitConfig().url).with_middlewares(
    SmartRetryMiddleware(
        default_retry_count=5,
        default_delay=5,
        use_jitter=True,
        use_delay_exponent=True,
        max_delay_exponent=300,
    ),
)

__all__ = ["broker"]
