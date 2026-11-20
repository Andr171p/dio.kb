import base64
import logging

import orjson
from openai import AsyncOpenAI

from src.application.indexing.image_analysis import ImageAnalysis
from src.application.indexing.models import MediaObject

from . import prompts
from .config import AiTunnelConfig

logger = logging.getLogger(__name__)


class AiTunnelImageAnalyzer:
    def __init__(self, config: AiTunnelConfig) -> None:
        self._config = config
        self._client = AsyncOpenAI(
            api_key=config.api_key.get_secret_value(),
            base_url=str(config.base_url),
            timeout=float(config.timeout),
            max_retries=config.max_retries,
        )

    @property
    def version(self) -> str:
        return f"{self._config.vision_model}:v{prompts.VERSION}"

    async def analyze(self, image: MediaObject) -> ImageAnalysis:
        if not image.content:
            raise ValueError("Image content cannot be empty")

        encoded = base64.b64encode(image.content).decode("ascii")
        data_url = f"data:{image.content_type};base64,{encoded}"

        response = await self._client.chat.completions.create(
            model=self._config.vision_model,
            response_format={"type": "json_object"},
            temperature=0,
            messages=[
                {"role": "system", "content": prompts.IMAGE_ANALYZER},
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                },
            ],
        )

        raw_content = response.choices[0].message.content if response.choices else None
        if not raw_content:
            logger.warning("Vision model returned empty content")
            return ImageAnalysis(text="", description="")

        return _parse_response(raw_content)


def _parse_response(raw_content: str) -> ImageAnalysis:
    try:
        payload = orjson.loads(raw_content)
    except orjson.JSONDecodeError:
        logger.warning("Vision model returned non-JSON response")
        return ImageAnalysis(text="", description=raw_content.strip())

    if not isinstance(payload, dict):
        logger.warning("Vision model returned JSON that is not an object: %s", type(payload).__name__)
        return ImageAnalysis(text="", description=raw_content.strip())

    text = str(payload.get("text") or "").strip()
    description = str(payload.get("description") or "").strip()
    return ImageAnalysis(text=text, description=description)
