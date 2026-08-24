import importlib

import pytest
from PIL import Image

from ebl.common.application.image_limits import (
    MAX_FRAGMENT_IMAGE_PIXELS,
    fragment_image_pixel_limit,
)


def test_default_limit_is_bounded():
    assert isinstance(MAX_FRAGMENT_IMAGE_PIXELS, int)
    assert MAX_FRAGMENT_IMAGE_PIXELS > 0


def test_limit_is_applied_inside_the_context():
    with fragment_image_pixel_limit():
        assert Image.MAX_IMAGE_PIXELS == MAX_FRAGMENT_IMAGE_PIXELS


def test_custom_limit_is_applied_inside_the_context():
    with fragment_image_pixel_limit(1234):
        assert Image.MAX_IMAGE_PIXELS == 1234


def test_previous_limit_is_restored():
    previous_limit = Image.MAX_IMAGE_PIXELS

    with fragment_image_pixel_limit():
        pass

    assert Image.MAX_IMAGE_PIXELS == previous_limit


def test_previous_limit_is_restored_after_an_error():
    previous_limit = Image.MAX_IMAGE_PIXELS

    with pytest.raises(RuntimeError):
        with fragment_image_pixel_limit():
            raise RuntimeError("failure inside the context")

    assert Image.MAX_IMAGE_PIXELS == previous_limit


@pytest.mark.parametrize("limit", [0, -1])
def test_non_positive_limit_is_rejected(limit):
    previous_limit = Image.MAX_IMAGE_PIXELS

    with pytest.raises(ValueError, match="must be positive"):
        with fragment_image_pixel_limit(limit):
            pass

    assert Image.MAX_IMAGE_PIXELS == previous_limit


def test_importing_the_annotations_service_does_not_disable_protection():
    importlib.import_module("ebl.fragmentarium.application.annotations_service")

    assert Image.MAX_IMAGE_PIXELS is not None


def test_importing_the_ebl_ai_client_does_not_disable_protection():
    importlib.import_module("ebl.ebl_ai_client")

    assert Image.MAX_IMAGE_PIXELS is not None
