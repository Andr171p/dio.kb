"""
Структурное разбиение Markdown на поисковые фрагменты.

``target_chars`` — мягкий лимит: неделимые блоки сохраняются целиком.
Исходная редакция статьи остаётся источником истины.
"""

import re
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from uuid import UUID, uuid5

from markdown_it import MarkdownIt
from markdown_it.token import Token

MEDIA_SCHEME = "media://"
DEFAULT_TARGET_CHARS = 1600

_PARSER = MarkdownIt("commonmark").enable(("table", "strikethrough"))

_FENCE_OPEN = re.compile(r"^ {0,3}(?P<marker>`{3,}|~{3,})")

_MIN_FENCE_LINES = 3
_MIN_TABLE_LINES = 2


@dataclass(frozen=True, slots=True)
class MarkdownChunk:
    """Фрагмент Markdown с контекстом раздела."""
    heading_path: tuple[str, ...]
    anchor: str | None
    markdown: str
    media_ids: tuple[UUID, ...] = ()


@dataclass(frozen=True, slots=True)
class _Block:
    """Внутреннее представление Markdown-блока."""
    kind: str
    markdown: str
    heading_path: tuple[str, ...]
    anchor: str | None
    media_ids: tuple[UUID, ...]
    list_items: tuple[str, ...] = ()


def heading_anchor(title: str) -> str:
    """Базовый slug заголовка."""

    normalized = re.sub(r"[^\w\s-]", "", title.casefold().strip())
    return re.sub(r"\s+", "-", normalized).strip("-") or "section"


def parse_media_id(src: str) -> UUID | None:
    """Извлекает UUID из media://<uuid>."""

    if not src.startswith(MEDIA_SCHEME):
        return None

    try:
        return UUID(src[len(MEDIA_SCHEME):])
    except ValueError:
        return None


def _groups(tokens: Sequence[Token]) -> Iterator[list[Token]]:
    """Группирует токены в верхнеуровневые блоки."""

    group: list[Token] = []

    for token in tokens:
        if group and token.level == 0 and token.nesting != -1:
            yield group
            group = []

        group.append(token)

    if group:
        yield group


def _collect_media_ids(tokens: Sequence[Token]) -> tuple[UUID, ...]:
    """Собирает media:// ссылки из изображений и ссылок."""

    ids: dict[UUID, None] = {}

    for token in tokens:
        for child in token.children or ():
            if child.type == "image":
                src = child.attrGet("src")
            elif child.type == "link_open":
                src = child.attrGet("href")
            else:
                continue

            if src and (media_id := parse_media_id(str(src))) is not None:
                ids[media_id] = None

    return tuple(ids)


def _title(token: Token) -> str:
    """Извлекает текст заголовка без Markdown-разметки."""

    return "".join(
        " " if child.type in {"softbreak", "hardbreak"}
        else child.content
        for child in token.children or ()
        if child.type in {
            "text",
            "code_inline",
            "image",
            "softbreak",
            "hardbreak",
            "html_inline",
        }
    ).strip()


def _blocks(content: str, tokens: Sequence[Token]) -> Iterator[_Block]:
    """Преобразует токены в блоки с контекстом заголовков."""

    lines = content.split("\n")
    headings: list[tuple[int, str]] = []
    anchors: dict[str, int] = {}
    anchor: str | None = None

    for group in _groups(tokens):
        first = group[0]

        if first.type == "heading_open":
            level = int(first.tag[1:])
            title = _title(group[1])

            while headings and headings[-1][0] >= level:
                headings.pop()

            headings.append((level, title))

            base = heading_anchor(title)
            count = anchors.get(base, 0)
            anchors[base] = count + 1

            anchor = base if count == 0 else f"{base}-{count}"
            continue

        if first.map is None:
            continue

        start, end = first.map
        markdown = "\n".join(lines[start:end]).strip("\n")

        if not markdown.strip():
            continue

        items: tuple[str, ...] = ()

        if first.type in {"bullet_list_open", "ordered_list_open"}:
            items = tuple(
                "\n".join(lines[item.map[0]:item.map[1]]).strip("\n")
                for item in group
                if item.type == "list_item_open" and item.level == first.level + 1 and item.map is not None
            )

        yield _Block(
            kind=first.type,
            markdown=markdown,
            heading_path=tuple(title for _, title in headings),
            anchor=anchor,
            media_ids=_collect_media_ids(group),
            list_items=items,
        )


def _pack(
    units: Sequence[str],
    target_chars: int,
    *,
    prefix: Sequence[str] = (),
    suffix: Sequence[str] = (),
) -> Iterator[str]:
    """Упаковывает структурные единицы в части.

    Неделимая единица может превышать ``target_chars``.
    """

    current: list[str] = []

    def render(selected: Sequence[str]) -> str:
        return "\n".join((*prefix, *selected, *suffix))

    for unit in units:
        if current and len(render((*current, unit))) > target_chars:
            yield render(current)
            current = []

        current.append(unit)

    if current:
        yield render(current)


def _fence_parts(markdown: str) -> tuple[str, list[str], str] | None:
    """Извлекает обрамление закрытого fenced code."""

    lines = markdown.split("\n")

    if len(lines) < _MIN_FENCE_LINES:
        return None

    if (match := _FENCE_OPEN.match(lines[0])) is None:
        return None

    marker = match.group("marker")
    char = marker[0]

    closing_pattern = (
        r" {0,3}"
        + re.escape(char)
        + "{"
        + str(len(marker))
        + r",}[ \t]*"
    )

    if not re.fullmatch(closing_pattern, lines[-1]):
        return None

    return lines[0], lines[1:-1], lines[-1]


def _split_block(  # noqa: C901
    block: _Block,
    target_chars: int,
    env: dict,
) -> Iterator[tuple[str, tuple[UUID, ...]]]:
    """Разбивает большой блок с учётом Markdown-структуры.
    Возвращает Markdown и относящиеся к части медиа.
    """

    if len(block.markdown) <= target_chars:
        yield block.markdown, block.media_ids
        return

    if block.kind == "table_open":
        lines = block.markdown.split("\n")

        if len(lines) > _MIN_TABLE_LINES:
            for part in _pack(lines[2:], target_chars, prefix=lines[:2]):
                yield part, _collect_media_ids(_PARSER.parse(part, dict(env)))
            return

    if block.kind in {"bullet_list_open", "ordered_list_open"} and block.list_items:
        for part in _pack(block.list_items, target_chars):
            yield part, _collect_media_ids(_PARSER.parse(part, dict(env)))
        return

    if block.kind == "fence":
        fence = _fence_parts(block.markdown)

        if fence is not None:
            opening, body, closing = fence

            if body:
                for part in _pack(body, target_chars, prefix=(opening,), suffix=(closing,)):
                    yield part, ()
                return

    # Не разрушаем неподдерживаемые блоки
    # только ради ограничения длины.
    yield block.markdown, block.media_ids


def split_markdown(content: str, *, target_chars: int = DEFAULT_TARGET_CHARS) -> list[MarkdownChunk]:
    """
    Разбивает Markdown на фрагменты по секциям заголовков.
    Не смешивает разные секции. Сохраняет структуру таблиц, списков и fenced code.
    """

    if target_chars <= 0:
        raise ValueError("target_chars must be positive")

    content = content.replace("\r\n", "\n").replace("\r", "\n")

    env: dict = {}
    tokens = _PARSER.parse(content, env)

    chunks: list[MarkdownChunk] = []
    parts: list[str] = []
    media_ids: list[UUID] = []

    section: tuple[tuple[str, ...], str | None] | None = None

    def flush() -> None:
        if parts and section is not None:
            chunks.append(
                MarkdownChunk(
                    heading_path=section[0],
                    anchor=section[1],
                    markdown="\n\n".join(parts),
                    media_ids=tuple(dict.fromkeys(media_ids)),
                )
            )

        parts.clear()
        media_ids.clear()

    for block in _blocks(content, tokens):
        block_section = (block.heading_path, block.anchor)

        for part, part_ids in _split_block(block, target_chars, env):
            if section != block_section or (parts and len("\n\n".join((*parts, part))) > target_chars):
                flush()

            section = block_section
            parts.append(part)
            media_ids.extend(part_ids)

            if len(part) > target_chars:
                flush()

    flush()
    return chunks


def chunk_id(article_id: UUID, revision_id: UUID, position: int) -> UUID:
    """Детерминированный ID чанка в пределах одной редакции."""

    if position < 0:
        raise ValueError("position must be non-negative")

    return uuid5(article_id, f"{revision_id}:{position}")


__all__ = [
    "DEFAULT_TARGET_CHARS",
    "MEDIA_SCHEME",
    "MarkdownChunk",
    "chunk_id",
    "heading_anchor",
    "parse_media_id",
    "split_markdown",
]
