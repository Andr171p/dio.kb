from io import BytesIO

import pytest
from PIL import Image, UnidentifiedImageError

from src.infra.services.media.images import validate_image


def test_image_pixel_limit_and_invalid_input():
    output = BytesIO()
    Image.new("RGB", (4, 3)).save(output, format="PNG")
    validate_image(output.getvalue(), 12)
    with pytest.raises(ValueError, match="pixel limit"):
        validate_image(output.getvalue(), 11)
    with pytest.raises(UnidentifiedImageError):
        validate_image(b"not an image", 100)
