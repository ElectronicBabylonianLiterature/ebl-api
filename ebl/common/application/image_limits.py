from contextlib import contextmanager
from typing import Iterator

from PIL import Image

MAX_FRAGMENT_IMAGE_PIXELS = 500_000_000


@contextmanager
def fragment_image_pixel_limit(
    limit: int = MAX_FRAGMENT_IMAGE_PIXELS,
) -> Iterator[None]:
    if limit <= 0:
        raise ValueError(f"Image pixel limit must be positive, got {limit}.")

    previous_limit = Image.MAX_IMAGE_PIXELS
    Image.MAX_IMAGE_PIXELS = limit
    try:
        yield
    finally:
        Image.MAX_IMAGE_PIXELS = previous_limit
