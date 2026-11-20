from io import BytesIO

from PIL import Image


def validate_image(content: bytes, max_pixels: int) -> None:
    """Reject malformed images and images larger than the configured pixel limit."""
    with Image.open(BytesIO(content)) as image:
        if image.width * image.height > max_pixels:
            raise ValueError("Image exceeds the pixel limit")
        image.verify()
