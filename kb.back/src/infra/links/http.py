
import asyncio
import logging
from http import HTTPStatus

import aiohttp
from ddf.infra.cache import InMemoryCache
from yarl import URL

from src.application.links.config import LinkPreviewConfig
from src.application.links.dtos import LinkPreview

from .exceptions import LinkPreviewUnavailableError
from .html import parse_link_preview
from .security import PublicOnlyResolver, validate_public_url

logger = logging.getLogger(__name__)

_REDIRECT_STATUSES = frozenset({
    HTTPStatus.MOVED_PERMANENTLY,   # 301
    HTTPStatus.FOUND,               # 302
    HTTPStatus.SEE_OTHER,           # 303
    HTTPStatus.TEMPORARY_REDIRECT,  # 307
    HTTPStatus.PERMANENT_REDIRECT,  # 308
})
_HTML_TYPES = frozenset({"text/html", "application/xhtml+xml"})
_USER_AGENT = "DIOS-KB-LinkPreview/1.0"


async def _read_prefix(response: aiohttp.ClientResponse, max_bytes: int) -> bytes:
    """Читает не более ``max_bytes`` распакованного HTTP-содержимого."""

    content = bytearray()

    async for part in response.content.iter_chunked(16 * 1024):
        remaining = max_bytes - len(content)
        content.extend(part[:remaining])

        if len(content) >= max_bytes:
            break

    return bytes(content)


class HttpLinkPreviewFetcher:
    def __init__(self, config: LinkPreviewConfig) -> None:
        self._config = config
        self._session: aiohttp.ClientSession | None = None
        self._session_lock = asyncio.Lock()

        self._semaphore = asyncio.Semaphore(config.max_concurrent_fetches)

        self._cache = InMemoryCache[LinkPreview]()

    async def fetch(self, raw_url: str) -> LinkPreview:
        """Получает превью с кешированием и проверкой SSRF."""

        url = validate_public_url(raw_url, max_chars=self._config.max_url_chars)
        key = str(url)

        if (cached := await self._cache.get(key)) is not None:
            return cached

        try:
            async with self._semaphore:
                preview = await self._load(url)

            ttl = self._config.cache_ttl_seconds

        except (aiohttp.ClientError, TimeoutError, UnicodeError, LinkPreviewUnavailableError) as exc:
            logger.info("Link preview unavailable", extra={"host": url.host, "error": type(exc).__name__})

            preview = LinkPreview(url=key, site_name=url.host)
            ttl = self._config.failure_cache_ttl_seconds

        await self._cache.set(key, preview, ttl=ttl)
        return preview

    async def _load(self, url: URL) -> LinkPreview:
        session = await self._get_session()

        for _ in range(self._config.max_redirects + 1):
            url = validate_public_url(str(url), max_chars=self._config.max_url_chars,)

            async with session.get(url, allow_redirects=False) as response:
                if response.status in _REDIRECT_STATUSES:
                    location = response.headers.get("Location")

                    if not location:
                        raise LinkPreviewUnavailableError("Redirect without Location")

                    url = validate_public_url(str(url.join(URL(location))), max_chars=self._config.max_url_chars)
                    continue

                if response.status != HTTPStatus.OK or response.content_type not in _HTML_TYPES:
                    raise LinkPreviewUnavailableError("Unsupported HTTP response")

                body = await _read_prefix(response, self._config.max_body_bytes)

                try:
                    html = body.decode(response.charset or "utf-8", errors="replace")
                except LookupError:
                    html = body.decode("utf-8", errors="replace")

                return parse_link_preview(
                    url,
                    html,
                    max_text_chars=self._config.max_text_chars,
                    max_url_chars=self._config.max_url_chars,
                )

        raise LinkPreviewUnavailableError("Maximum redirects exceeded")

    async def _get_session(self) -> aiohttp.ClientSession:
        """Лениво создаёт одну сессию на экземпляр."""

        async with self._session_lock:
            if self._session is None or self._session.closed:
                connector = aiohttp.TCPConnector(
                    resolver=PublicOnlyResolver(),
                    use_dns_cache=False,
                    limit=self._config.max_connections,
                    limit_per_host=2,
                )
                timeout = aiohttp.ClientTimeout(total=self._config.timeout_seconds)
                headers = {"User-Agent": _USER_AGENT, "Accept": "text/html,application/xhtml+xml"}

                self._session = aiohttp.ClientSession(
                    connector=connector,
                    timeout=timeout,
                    headers=headers,
                    cookie_jar=aiohttp.DummyCookieJar(),
                    trust_env=False,
                )

            return self._session

    async def close(self) -> None:
        async with self._session_lock:
            if self._session is not None:
                await self._session.close()
                self._session = None
