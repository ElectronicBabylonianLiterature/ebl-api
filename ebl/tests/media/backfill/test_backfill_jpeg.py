import io
from collections.abc import Callable

import pytest
from PIL import Image

from ebl.media.application.backfill_plan import BackfillPolicy, SourceRejected
from ebl.media.application.media_requests import BackfillRequest
from ebl.media.infrastructure.backfill_images import inspect_image
from ebl.media.infrastructure.backfill_jpeg import inspect_jpeg
from ebl.tests.media.backfill.conftest import image_bytes


def test_structural_jpeg_verification_preserves_global_pixel_limit() -> None:
    content = bytearray(image_bytes())
    position = content.index(b"\xff\xc0")
    dimension_offset = position + 5
    dimension_end = dimension_offset + 4
    content[dimension_offset:dimension_end] = b"\x75\x30\x75\x30"
    original_limit = Image.MAX_IMAGE_PIXELS
    representation, _evidence = inspect_image(
        io.BytesIO(bytes(content)), len(content), BackfillPolicy()
    )
    assert representation.width == representation.height == 30_000
    assert Image.MAX_IMAGE_PIXELS == original_limit


def test_embedded_eoi_is_not_main_image_eoi() -> None:
    source = image_bytes()[:-2]
    embedded = source[:2] + b"\xff\xe2\x00\x04\xff\xd9" + source[2:]
    with pytest.raises(SourceRejected, match="malformed"):
        inspect_jpeg(io.BytesIO(embedded), len(embedded))


def test_trailing_bytes_after_main_eoi_are_preserved() -> None:
    source = image_bytes() + b"trailing metadata"
    assert inspect_jpeg(io.BytesIO(source), len(source))[:2] == (16, 12)


def test_large_jpeg_is_imported_with_deferred_previews(
    legacy_photo: Callable, migration_factory: Callable
) -> None:
    legacy_photo()
    migration = migration_factory(BackfillPolicy(generate_previews=True, max_pixels=10))
    candidate = tuple(migration.plan_batch(BackfillRequest()))[0]
    assert candidate.outcome == "candidate"
    assert candidate.reason == "preview-deferred-pixel-limit"
    applied = migration.apply(candidate)
    assert applied.outcome == "created"


def test_attribution_is_mapped_by_default(
    legacy_photo: Callable, migration_factory: Callable
) -> None:
    exif = Image.Exif()
    exif[315] = "Photographer"
    exif[33432] = "Museum credit"
    legacy_photo(content=image_bytes(exif=exif.tobytes()))
    candidate = tuple(migration_factory().plan_batch(BackfillRequest()))[0]
    assert candidate.attribution == "Artist: Photographer\nCopyright: Museum credit"
    assert candidate.attribution_evidence == {
        "Artist": "Photographer",
        "Copyright": "Museum credit",
    }
