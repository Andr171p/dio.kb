"""Безопасная работа с URL."""

import ipaddress
import re
import socket

import aiohttp
from aiohttp.abc import AbstractResolver, ResolveResult
from yarl import URL

from .exceptions import UnsafeLinkError

_DEFAULT_MAX_URL_LENGTH = 2048

_HTTP_DEFAULT_PORT = 80
_HTTPS_DEFAULT_PORT = 443

_ASCII_MIN_PRINTABLE = 32
_ASCII_DEL_CHAR = 127


def ensure_public_ip(address: str) -> None:
    """Запрещает все специальные и непубличные IP."""

    try:
        ip = ipaddress.ip_address(address)
    except ValueError as exc:
        raise UnsafeLinkError("Invalid resolved IP address") from exc

    if not ip.is_global:
        raise UnsafeLinkError("Non-public IP address")


def validate_public_url(raw: str, *, max_chars: int = 2048) -> URL:  # noqa: C901
    """Валидирует HTTP URL без предварительного DNS-запроса."""

    if (
        not raw
        or len(raw) > max_chars
        or "\\" in raw
        or any(ord(char) < _ASCII_MIN_PRINTABLE or ord(char) == _ASCII_DEL_CHAR for char in raw)
    ):
        raise UnsafeLinkError("Invalid URL")

    try:
        url = URL(raw)
        host, port = url.host, url.port
    except (ValueError, UnicodeError) as exc:
        raise UnsafeLinkError("Invalid URL") from exc

    if url.scheme not in {"http", "https"} or not host:
        raise UnsafeLinkError("Only absolute HTTP(S) URLs are allowed")

    if url.user is not None or url.password is not None:
        raise UnsafeLinkError("URL credentials are not allowed")

    expected_port = _HTTPS_DEFAULT_PORT if url.scheme == "https" else _HTTP_DEFAULT_PORT
    if port != expected_port:
        raise UnsafeLinkError("Non-standard HTTP port")

    hostname = host.lower()

    if hostname == "localhost" or hostname.endswith((".localhost", ".local")):
        raise UnsafeLinkError("Local hostnames are not allowed")

    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        # Нестандартные числовые IPv4-записи, например
        # 127.1 или 2130706433, запрещаем полностью.
        if re.fullmatch(r"[0-9.]+", host):
            raise UnsafeLinkError("Non-canonical IP address") from None
    else:
        if not ip.is_global:
            raise UnsafeLinkError("Non-public IP address")

    # Fragment никогда не отправляется HTTP-серверу.
    return url.with_fragment(None)


class PublicOnlyResolver(AbstractResolver):
    """Проверяет все IP, полученные при DNS resolution."""

    def __init__(self) -> None:
        self._resolver = aiohttp.DefaultResolver()

    async def resolve(
        self,
        host: str,
        port: int = 0,
        family: socket.AddressFamily = socket.AF_INET,
    ) -> list[ResolveResult]:
        results = await self._resolver.resolve(host, port, family)

        if not results:
            raise UnsafeLinkError("DNS returned no addresses")

        for result in results:
            ensure_public_ip(result["host"])

        return results

    async def close(self) -> None:
        await self._resolver.close()
