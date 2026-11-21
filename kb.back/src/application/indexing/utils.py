from collections.abc import AsyncIterator


class MediaTooLargeError(ValueError):
    pass


async def read_limited(chunks: AsyncIterator[bytes], *, max_bytes: int) -> bytes:
    """Читает поток не превышая установленный лимит."""

    if max_bytes <= 0:
        raise ValueError("max_bytes must be positive.")

    parts: list[bytes] = []
    size = 0

    async for chunk in chunks:
        size += len(chunk)

        if size > max_bytes:
            raise MediaTooLargeError(f"Media exceeds {max_bytes} bytes.")

        parts.append(chunk)

    return b"".join(parts)
