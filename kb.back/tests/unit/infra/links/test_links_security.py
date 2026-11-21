
import pytest
from yarl import URL

from src.infra.links.exceptions import UnsafeLinkError
from src.infra.links.html import parse_link_preview
from src.infra.links.security import validate_public_url


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1",
        "http://127.1",
        "http://2130706433",
        "http://169.254.169.254",
        "http://[::1]",
        "http://localhost",
        "http://example.com:8080",
        "file:///etc/passwd",
        "http://user:password@example.com",
    ],
)
def test_unsafe_urls_rejected(url: str) -> None:
    with pytest.raises(UnsafeLinkError):
        validate_public_url(url)


def test_private_og_image_is_rejected() -> None:
    html = """
    <head>
      <meta property="og:title" content="Documentation">
      <meta property="og:image"
            content="http://127.0.0.1/internal.png">
    </head>
    """

    preview = parse_link_preview(URL("https://example.com/docs"), html)

    assert preview.title == "Documentation"
    assert preview.image_url is None
