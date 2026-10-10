"""
Разбиение Markdown на поисковые фрагменты с учётом структуры документа.

Документ разбирается в AST (markdown-it), верхнеуровневые блоки (абзацы, списки, таблицы,
код, цитаты) группируются по секциям заголовков и упаковываются во фрагменты до ``max_chars``.
Блок не разрезается, пока помещается целиком; большой блок режется по строкам,
у таблиц при этом повторяется шапка.
"""

import re
import uuid
from collections.abc import Iterator
from dataclasses import dataclass, field
from uuid import UUID

from markdown_it import MarkdownIt
from markdown_it.token import Token

MEDIA_SCHEME = "media://"
DEFAULT_MAX_CHARS = 1600
# Шапка Markdown-таблицы: строка заголовков + разделитель
_TABLE_HEADER_LINES = 2

_parser = MarkdownIt("commonmark").enable(["table", "strikethrough"])


@dataclass(frozen=True, slots=True)
class MarkdownChunk:
    heading_path: tuple[str, ...]
    anchor: str | None
    text: str
    media_ids: tuple[UUID, ...] = ()


@dataclass(slots=True)
class _Block:
    heading_path: tuple[str, ...]
    anchor: str | None
    kind: str
    text: str
    media_ids: list[UUID] = field(default_factory=list)


def heading_anchor(title: str) -> str:
    """Якорь заголовка в стиле GitHub: lower-case, без пунктуации, пробелы → дефисы."""

    slug = re.sub(r"[^\w\- ]", "", title.strip().lower())
    return slug.replace(" ", "-")


def parse_media_id(src: str) -> UUID | None:
    """Идентификатор медиа из стабильной ссылки ``media://<uuid>``."""

    if not src.startswith(MEDIA_SCHEME):
        return None

    try:
        return UUID(src.removeprefix(MEDIA_SCHEME).strip("/"))
    except ValueError:
        return None


def _iter_top_level_blocks(tokens: list[Token]) -> Iterator[list[Token]]:
    group: list[Token] = []

    for token in tokens:
        if token.level == 0 and token.nesting != -1 and group:
            yield group
            group = []
        group.append(token)

    if group:
        yield group


def _collect_media_ids(tokens: list[Token]) -> list[UUID]:
    sources = (
        str(child.attrs.get("src", ""))
        for token in tokens
        for child in token.children or ()
        if child.type == "image"
    )
    return [media_id for source in sources if (media_id := parse_media_id(source))]


def _parse_blocks(content: str) -> list[_Block]:
    lines = content.splitlines()
    headings: list[tuple[int, str]] = []
    anchor_counts: dict[str, int] = {}
    anchor: str | None = None
    blocks: list[_Block] = []

    for group in _iter_top_level_blocks(_parser.parse(content)):
        first = group[0]

        if first.type == "heading_open":
            level = int(first.tag[1])
            title = group[1].content.strip() if len(group) > 1 else ""

            while headings and headings[-1][0] >= level:
                headings.pop()
            headings.append((level, title))

            base = heading_anchor(title)
            count = anchor_counts.get(base, 0)
            anchor_counts[base] = count + 1
            anchor = base if count == 0 else f"{base}-{count}"
            continue

        if first.map is None:
            continue

        text = "\n".join(lines[first.map[0] : first.map[1]]).strip()
        if not text:
            continue

        blocks.append(
            _Block(
                heading_path=tuple(title for _, title in headings),
                anchor=anchor,
                kind=first.type,
                text=text,
                media_ids=_collect_media_ids(group),
            )
        )

    return blocks


def _split_oversized(block: _Block, max_chars: int) -> list[str]:
    lines = block.text.splitlines()
    header = (
        lines[:_TABLE_HEADER_LINES] if block.kind == "table_open" and len(lines) > _TABLE_HEADER_LINES else []
    )
    body = lines[len(header) :]

    parts: list[str] = []
    current: list[str] = list(header)

    for line in body:
        if current[len(header) :] and len("\n".join([*current, line])) > max_chars:
            parts.append("\n".join(current))
            current = list(header)
        current.append(line)

    if current[len(header) :]:
        parts.append("\n".join(current))

    return parts


def split_markdown(content: str, *, max_chars: int = DEFAULT_MAX_CHARS) -> list[MarkdownChunk]:
    """Разбивает Markdown на фрагменты, не смешивая разные секции заголовков."""

    chunks: list[MarkdownChunk] = []
    texts: list[str] = []
    media_ids: list[UUID] = []
    section: tuple[tuple[str, ...], str | None] | None = None

    def flush() -> None:
        if texts and section is not None:
            chunks.append(
                MarkdownChunk(
                    heading_path=section[0],
                    anchor=section[1],
                    text="\n\n".join(texts),
                    media_ids=tuple(dict.fromkeys(media_ids)),
                )
            )
        texts.clear()
        media_ids.clear()

    for block in _parse_blocks(content):
        block_section = (block.heading_path, block.anchor)
        if block_section != section or len("\n\n".join([*texts, block.text])) > max_chars:
            flush()
            section = block_section

        if len(block.text) <= max_chars:
            texts.append(block.text)
            media_ids.extend(block.media_ids)
            continue

        for part in _split_oversized(block, max_chars):
            texts.append(part)
            media_ids.extend(block.media_ids)
            flush()

    flush()
    return chunks


def chunk_id(article_id: UUID, revision_id: UUID, position: int) -> UUID:
    """Детерминированный идентификатор фрагмента: повторная индексация идемпотентна."""

    return uuid.uuid5(article_id, f"{revision_id}:{position}")


__all__ = ["MEDIA_SCHEME", "MarkdownChunk", "chunk_id", "heading_anchor", "parse_media_id", "split_markdown"]
