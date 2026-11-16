from io import BytesIO
from PIL import Image


def image_bytes(format: str = "PNG", size: tuple[int, int] = (96, 48)) -> bytes:
    with BytesIO() as content, Image.new("RGB", size, "red") as image:
        image.save(content, format=format)
        return content.getvalue()
