from collections.abc import Awaitable, Callable, Sequence

type TextEmbedder = Callable[[str], Awaitable[Sequence[float]]]

__all__ = ["TextEmbedder"]
