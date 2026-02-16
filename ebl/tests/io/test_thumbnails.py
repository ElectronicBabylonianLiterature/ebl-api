import pytest
from PIL import Image
from ebl.fragmentarium.application.fragment_finder import ThumbnailSize
from ebl.io.fragments.thumbnails import resize


@pytest.fixture
def large_image():
    return Image.new("RGB", (1200, 3800))


@pytest.mark.parametrize("size", ThumbnailSize)
def test_resize(large_image, size):
    resized = resize(large_image, size)

    assert resized.size[0] == size.value
