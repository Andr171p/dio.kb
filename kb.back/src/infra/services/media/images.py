from io import BytesIO

from PIL import Image


def validate_image(content: bytes, max_pixels: int) -> None:
    """
    Отклоняйте некорректно сформированные изображения,
    а также изображения, размер которых превышает заданный лимит в пикселях.
    """
    with Image.open(BytesIO(content)) as image:
        if image.width * image.height > max_pixels:
            raise ValueError("Image exceeds the pixel limit")
        image.verify()
