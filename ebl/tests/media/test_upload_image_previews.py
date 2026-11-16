from contextlib import ExitStack
from io import BytesIO
from typing import Literal

import pytest
from PIL import Image

from ebl.media.domain import MediaId
from ebl.media.application.media_storage_identity import StoredRepresentationHandle
from ebl.media.infrastructure import upload_images
from ebl.media.infrastructure.upload_images import (
    UploadLimits,
    UploadValidationError,
    prepare_upload,
    write_prepared,
)
from ebl.media.infrastructure.upload_previews import (
    LANCZOS_RESAMPLING,
    eight_bit,
    preview,
)
from ebl.tests.media.in_memory_representation_store import InMemoryRepresentationStore
from ebl.tests.media.upload_image_fixtures import image_bytes


@pytest.mark.parametrize("mode", ["I", "F"])
def test_high_bit_depth_previews_scale_samples(mode: Literal["I", "F"]) -> None:
    source = Image.new(mode, (1, 1), 32768)
    with eight_bit(source) as converted:
        assert converted.mode == "L"
        assert converted.getpixel((0, 0)) == 128
    source.close()


@pytest.mark.parametrize("mode", ["RGBA", "P"])
def test_transparent_previews_flatten_onto_white(mode: Literal["RGBA", "P"]) -> None:
    with Image.new(mode, (4, 4)) as source, ExitStack() as stack:
        if mode == "P":
            source.info["transparency"] = 0
        result = preview(source, 4, stack)
        assert result.representation.mime_type == "image/jpeg"
        with Image.open(result.content) as decoded:
            assert decoded.getpixel((0, 0)) == (255, 255, 255)
    assert result.content.closed


@pytest.mark.parametrize("length", [0, -1, True])
def test_nonpositive_or_boolean_content_length_is_rejected(length: int) -> None:
    with pytest.raises(UploadValidationError, match="must be positive"):
        with prepare_upload(BytesIO(image_bytes()), content_length=length):
            pytest.fail("Invalid length accepted")


def test_upload_pixel_limit_cannot_exceed_owned_store_safety_limit() -> None:
    with pytest.raises(ValueError, match="owned-store safety limit"):
        UploadLimits(max_pixels=40_000_001)


def test_mismatched_binary_signature_and_decoded_format_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(upload_images, "raster_mime_type", lambda content: "image/jpeg")
    with pytest.raises(UploadValidationError, match="binary content"):
        with prepare_upload(BytesIO(image_bytes())):
            pytest.fail("Mismatched format accepted")


def test_prepared_write_delegates_owned_handles_and_journal() -> None:
    store = InMemoryRepresentationStore()
    journal: list[StoredRepresentationHandle] = []
    identifier = MediaId.create()
    with prepare_upload(BytesIO(image_bytes())) as prepared:
        stored = write_prepared(prepared, store, identifier, journal.append)
    assert journal == [stored.original, stored.display] + [
        item.handle for item in stored.thumbnails
    ]


def test_previews_keep_the_existing_lanczos_filter() -> None:
    assert LANCZOS_RESAMPLING == 1
