"""HTML-парсер OpenGraph."""


from html.parser import HTMLParser

from yarl import URL

from src.application.links.dtos import LinkPreview

from .security import UnsafeLinkError, validate_public_url


class MetadataParser(HTMLParser):
    """Извлекает основные метаданные из HTML head."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)

        self.meta: dict[str, str] = {}
        self.title: str | None = None
        self.icon: str | None = None
        self.base: str | None = None

        self._in_head = True
        self._in_title = False
        self._title_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "body":
            self._in_head = False
            return

        if not self._in_head:
            return

        values = {key: value for key, value in attrs if value is not None}

        if tag == "meta":
            name = (values.get("property") or values.get("name") or "").lower()
            content = values.get("content", "").strip()

            if name and content:
                self.meta.setdefault(name, content)

        elif tag == "title":
            self._in_title = True

        elif tag == "link":
            rel = values.get("rel", "").lower().split()

            if "icon" in rel and values.get("href"):
                self.icon = self.icon or values["href"]

        elif tag == "base":
            self.base = self.base or values.get("href")

    def handle_endtag(self, tag: str) -> None:
        if tag == "title" and self._in_title:
            self._in_title = False
            self.title = (" ".join("".join(self._title_parts).split()) or None)
        elif tag == "head":
            self._in_head = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self._title_parts.append(data)


def _clip(value: str | None, max_chars: int) -> str | None:
    text = " ".join(value.split()) if value else ""

    if not text:
        return None

    if len(text) <= max_chars:
        return text

    return f"{text[:max_chars - 1]}…"


def _absolute_url(base: URL, value: str | None, max_url_chars: int) -> str | None:
    if not value:
        return None

    try:
        candidate = base.join(URL(value.strip()))
        return str(validate_public_url(str(candidate), max_chars=max_url_chars))
    except (UnsafeLinkError, ValueError, UnicodeError):
        return None


def parse_link_preview(
    url: URL,
    html: str,
    *,
    max_text_chars: int = 300,
    max_url_chars: int = 2048,
) -> LinkPreview:
    """Извлекает OpenGraph / HTML metadata без HTTP-запросов."""

    parser = MetadataParser()
    parser.feed(html)
    parser.close()

    meta = parser.meta

    base_url = URL(_absolute_url(url, parser.base, max_url_chars) or str(url))

    def link(*values: str | None) -> str | None:
        for value in values:
            if result := _absolute_url(base_url, value, max_url_chars):
                return result
        return None

    return LinkPreview(
        url=str(url),
        title=_clip(meta.get("og:title") or meta.get("twitter:title") or parser.title, max_text_chars),
        description=_clip(
            meta.get("og:description")
            or meta.get("twitter:description")
            or meta.get("description"),
            max_text_chars,
        ),
        image_url=link(meta.get("og:image"), meta.get("twitter:image")),
        site_name=_clip(meta.get("og:site_name"), max_text_chars) or url.host,
        favicon_url=link(parser.icon, "/favicon.ico"),
    )
