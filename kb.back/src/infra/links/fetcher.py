import contextlib
import ipaddress
import logging
import socket
from html.parser import HTMLParser
from http import HTTPStatus
from urllib.parse import urljoin, urlsplit

import aiohttp
from aiohttp.abc import AbstractResolver, ResolveResult
from ddf.infra.cache import InMemoryCache

from src.application.links.dtos import LinkPreviewResponse

logger = logging.getLogger(__name__)

_TIMEOUT_SECONDS = 5
_MAX_REDIRECTS = 3
_MAX_BODY_BYTES = 512 * 1024
_CACHE_TTL = 60 * 60
_FAILURE_CACHE_TTL = 5 * 60
_MAX_TEXT_LENGTH = 300
_USER_AGENT = "Mozilla/5.0 (compatible; DIOS-Knowledge-LinkPreview/1.0)"
_REDIRECT_STATUSES = frozenset({301, 302, 303, 307, 308})


class UnsafeAddressError(Exception):
    """Адрес ведёт во внутреннюю сеть или не является публичным HTTP(S)."""


def _ensure_public_ip(address: str) -> None:
    if not ipaddress.ip_address(address).is_global:
        raise UnsafeAddressError(f"Address {address} is not public.")


def _ensure_safe_url(url: str) -> None:
    parts = urlsplit(url)
    if parts.scheme not in {"http", "https"} or not parts.hostname:
        raise UnsafeAddressError("Only absolute http(s) URLs are allowed.")

    # IP-литералы aiohttp не передаёт в resolver — проверяем их до запроса
    with contextlib.suppress(ValueError):
        _ensure_public_ip(parts.hostname.strip("[]"))


class _PublicOnlyResolver(AbstractResolver):
    """Резолвер, отклоняющий непубличные адреса на каждом соединении (защита от DNS rebinding)."""

    def __init__(self) -> None:
        self._resolver = aiohttp.DefaultResolver()

    async def resolve(
        self, host: str, port: int = 0, family: socket.AddressFamily = socket.AF_INET
    ) -> list[ResolveResult]:
        results = await self._resolver.resolve(host, port, family)
        for result in results:
            _ensure_public_ip(result["host"])
        return results

    async def close(self) -> None:
        await self._resolver.close()


class _MetadataParser(HTMLParser):
    """Собирает <title>, <meta> и иконку из <head>."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.meta: dict[str, str] = {}
        self.title: str | None = None
        self.icon: str | None = None
        self._in_title = False
        self._title_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {name.lower(): value for name, value in attrs if value is not None}

        if tag == "meta":
            key = (values.get("property") or values.get("name") or "").lower()
            if key and "content" in values:
                self.meta.setdefault(key, values["content"].strip())
        elif tag == "link" and "icon" in values.get("rel", "").lower().split() and "href" in values:
            self.icon = self.icon or values["href"]
        elif tag == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "title" and self._in_title:
            self._in_title = False
            self.title = " ".join("".join(self._title_parts).split()) or None

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self._title_parts.append(data)


def _clip(value: str | None) -> str | None:
    if not value:
        return None
    value = " ".join(value.split())
    return value if len(value) <= _MAX_TEXT_LENGTH else f"{value[: _MAX_TEXT_LENGTH - 1]}…"


def _absolute_http_url(base: str, value: str | None) -> str | None:
    if not value:
        return None
    url = urljoin(base, value)
    return url if urlsplit(url).scheme in {"http", "https"} else None


def _to_preview(url: str, html: str) -> LinkPreviewResponse:
    parser = _MetadataParser()
    parser.feed(html)
    meta = parser.meta

    return LinkPreviewResponse(
        url=url,
        title=_clip(meta.get("og:title") or meta.get("twitter:title") or parser.title),
        description=_clip(
            meta.get("og:description") or meta.get("twitter:description") or meta.get("description")
        ),
        image_url=_absolute_http_url(url, meta.get("og:image") or meta.get("twitter:image")),
        site_name=_clip(meta.get("og:site_name")) or urlsplit(url).hostname,
        favicon_url=_absolute_http_url(url, parser.icon or "/favicon.ico"),
    )


class HttpLinkPreviewFetcher:
    """Загрузка OpenGraph-метаданных публичных страниц: только http(s), только публичные IP, лимиты."""

    def __init__(self) -> None:
        self._session: aiohttp.ClientSession | None = None
        self._cache = InMemoryCache[LinkPreviewResponse]()

    async def fetch(self, url: str) -> LinkPreviewResponse:
        if (cached := await self._cache.get(url)) is not None:
            return cached

        try:
            preview = await self._load(url)
            ttl = _CACHE_TTL
        except (UnsafeAddressError, aiohttp.ClientError, TimeoutError, UnicodeError) as exc:
            logger.info("Link preview unavailable for %s: %s", url, exc)
            preview, ttl = LinkPreviewResponse(url=url), _FAILURE_CACHE_TTL

        await self._cache.set(url, preview, ttl=ttl)
        return preview

    async def _load(self, url: str) -> LinkPreviewResponse:
        session = self._get_session()

        # Редиректы — вручную: каждый новый адрес проходит ту же проверку
        for _ in range(_MAX_REDIRECTS + 1):
            _ensure_safe_url(url)
            async with session.get(url, allow_redirects=False) as response:
                if response.status in _REDIRECT_STATUSES and "Location" in response.headers:
                    url = urljoin(url, response.headers["Location"])
                    continue

                if response.status != HTTPStatus.OK or response.content_type != "text/html":
                    return LinkPreviewResponse(url=url, site_name=urlsplit(url).hostname)

                body = await response.content.read(_MAX_BODY_BYTES)
                html = body.decode(response.get_encoding(), errors="replace")
                return _to_preview(url, html)

        raise UnsafeAddressError("Too many redirects.")

    def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(resolver=_PublicOnlyResolver(), limit=20),
                timeout=aiohttp.ClientTimeout(total=_TIMEOUT_SECONDS),
                headers={"User-Agent": _USER_AGENT, "Accept": "text/html,application/xhtml+xml"},
            )
        return self._session

    async def close(self) -> None:
        if self._session is not None:
            await self._session.close()
