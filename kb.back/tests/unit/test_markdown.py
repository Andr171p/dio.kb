from uuid import UUID

from src.application.search.markdown import split_markdown

MEDIA_ID = UUID("0198f2a0-0000-7000-8000-000000000001")
MAX_CHARS = 600


def test_chunks_follow_heading_sections_and_collect_media() -> None:
    content = f"""Вступление.

# Настройка VPN

Абзац ![схема](media://{MEDIA_ID}) и обычная ![картинка](https://example.com/x.png).

## Шаги

1. Скачать клиент

## Шаги

Повтор заголовка.
"""
    chunks = split_markdown(content)

    assert [(chunk.heading_path, chunk.anchor) for chunk in chunks] == [
        ((), None),
        (("Настройка VPN",), "настройка-vpn"),
        (("Настройка VPN", "Шаги"), "шаги"),
        (("Настройка VPN", "Шаги"), "шаги-1"),
    ]
    assert chunks[1].media_ids == (MEDIA_ID,)


def test_oversized_table_is_split_with_repeated_header() -> None:
    rows = "\n".join(f"| p{i} | {'значение ' * 10} |" for i in range(30))
    content = f"# Таблица\n\n| Параметр | Значение |\n|---|---|\n{rows}\n"

    chunks = split_markdown(content, max_chars=MAX_CHARS)

    assert len(chunks) > 1
    assert all(chunk.text.startswith("| Параметр | Значение |\n|---|---|") for chunk in chunks)
    assert all(len(chunk.text) <= MAX_CHARS for chunk in chunks)
