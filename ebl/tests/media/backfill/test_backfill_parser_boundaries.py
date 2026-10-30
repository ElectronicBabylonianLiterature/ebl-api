import io
from collections.abc import Callable

import pytest
from PIL import Image

from ebl.media.application.backfill_plan import BackfillPolicy, SourceRejected
from ebl.media.application.media_requests import BackfillRequest
from ebl.media.infrastructure.backfill_images import inspect_image, preview_bytes
from ebl.media.infrastructure.backfill_jpeg import inspect_jpeg
from ebl.media.infrastructure.backfill_jpeg_segments import exif_evidence, skip_entropy
from ebl.tests.media.backfill.conftest import image_bytes

FRAME = b"\xff\xc0\x00\x0b\x08\x00\x0c\x00\x10\x01\x01\x11\x00"
SCAN = b"\xff\xda\x00\x08\x01\x01\x00\x00\x3f\x00"


@pytest.mark.parametrize(
    "content",
    [
        b"broken",
        b"\xff\xd8A",
        b"\xff\xd8\xff\xff",
        b"\xff\xd8\xff\xd9",
        b"\xff\xd8\xff\xd8",
        b"\xff\xd8\xff\x00",
        b"\xff\xd8\xff\xd0",
        b"\xff\xd8\xff\xe0\x00",
        b"\xff\xd8\xff\xe0\x00\x01",
        b"\xff\xd8\xff\xe0\x00\x10",
        b"\xff\xd8\xff\xc0\x00\x02",
        b"\xff\xd8\xff\xda\x00\x02",
        b"\xff\xd8",
        b"\xff\xd8" + FRAME + SCAN + b"entropy without terminator",
        b"\xff\xd8" + FRAME + SCAN + b"\xff",
    ],
)
def test_truncated_or_invalid_jpeg_structure_is_blocked(content: bytes) -> None:
    with pytest.raises(SourceRejected, match="malformed-original"):
        inspect_jpeg(io.BytesIO(content), len(content))


def test_entropy_parser_handles_block_boundary_and_restart_markers() -> None:
    content = io.BytesIO(b"a" * 65_535 + b"\xff\x00\xff\xd0\xff\xd9")
    skip_entropy(content)
    assert content.read() == b"\xff\xd9"


def test_standalone_marker_does_not_consume_segment_length() -> None:
    content = image_bytes()
    content = content[:2] + b"\xff\x01" + content[2:]
    assert inspect_jpeg(io.BytesIO(content), len(content))[:2] == (16, 12)


def test_bytes_exif_evidence_preserves_literal_credit() -> None:
    exif = Image.Exif()
    exif[315] = b"  Photographer\x00"
    exif[33432] = 10
    assert exif_evidence(exif) == {"Artist": "Photographer"}


def test_unreadable_exif_is_reviewed(monkeypatch: pytest.MonkeyPatch) -> None:
    def unreadable(_self: Image.Exif, _payload: bytes) -> None:
        raise SyntaxError("invalid EXIF")

    monkeypatch.setattr(Image.Exif, "load", unreadable)
    content = b"\xff\xd8\xff\xe1\x00\x08Exif\x00\x00"
    with pytest.raises(SourceRejected, match="unreadable-attribution-metadata"):
        inspect_jpeg(io.BytesIO(content), len(content))


def without_quantization_tables(content: bytes) -> bytes:
    offset = 2
    result = content[:2]
    while content[offset + 1] != 0xDA:
        length_start = offset + 2
        length_end = length_start + 2
        length = int.from_bytes(content[length_start:length_end], "big") + 2
        segment_end = offset + length
        if content[offset + 1] != 0xDB:
            result += content[offset:segment_end]
        offset += length
    return result + content[offset:]


@pytest.mark.parametrize("previews", [False, True])
def test_missing_quantization_tables_are_blocked_without_aborting_plan(
    legacy_photo: Callable, migration_factory: Callable, previews: bool
) -> None:
    legacy_photo(content=without_quantization_tables(image_bytes()))
    result = tuple(
        migration_factory(BackfillPolicy(generate_previews=previews)).plan_batch(
            BackfillRequest()
        )
    )[0]
    assert (result.outcome, result.reason) == ("blocked", "malformed-original")


def test_preview_decode_failure_is_a_source_rejection() -> None:
    with pytest.raises(SourceRejected, match="preview-decode-failed"):
        preview_bytes(io.BytesIO(without_quantization_tables(image_bytes())), 240)


def test_animated_webp_is_reviewed() -> None:
    stream = io.BytesIO()
    Image.new("RGB", (2, 2), "red").save(
        stream,
        "WEBP",
        save_all=True,
        append_images=[Image.new("RGB", (2, 2), "blue")],
        duration=100,
    )
    with pytest.raises(SourceRejected, match="animated-original"):
        inspect_image(stream, len(stream.getvalue()), BackfillPolicy())
