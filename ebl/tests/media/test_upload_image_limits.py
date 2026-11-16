from io import BytesIO
from typing import BinaryIO, Literal, cast
import pytest
from PIL import Image
from ebl.media.infrastructure import upload_images
from ebl.media.infrastructure.upload_images import (
    UploadBusyError,
    UploadLimits,
    UploadTooLargeError,
    UploadValidationError,
    prepare_upload,
)

from ebl.tests.media.upload_image_fixtures import image_bytes


@pytest.mark.parametrize("declared", [1, 100000])
def test_rejects_length_mismatch(declared: int) -> None:
    with pytest.raises(UploadValidationError, match="length"):
        with prepare_upload(BytesIO(image_bytes()), content_length=declared):
            pytest.fail("Mismatched length accepted")


def test_prechecks_declared_oversize_without_reading() -> None:
    class NoReads(BytesIO):
        def read(self, size: int | None = -1) -> bytes:
            pytest.fail("Oversized request must not be read")

    with pytest.raises(UploadTooLargeError):
        with prepare_upload(
            NoReads(), content_length=101, limits=UploadLimits(max_bytes=100)
        ):
            pytest.fail("Oversize accepted")


def test_bounds_unknown_length_stream_reads() -> None:
    source = BytesIO(b"x" * 100000)
    with pytest.raises(UploadTooLargeError):
        with prepare_upload(source, limits=UploadLimits(max_bytes=100)):
            pytest.fail("Oversize accepted")
    assert source.tell() == 101


@pytest.mark.parametrize("format", ["PNG", "WEBP"])
def test_rejects_animated_content(format: str) -> None:
    content = BytesIO()
    with (
        Image.new("RGB", (20, 10), "red") as first,
        Image.new("RGB", (20, 10), "blue") as second,
    ):
        first.save(
            content, format=format, save_all=True, append_images=[second], duration=100
        )
    with pytest.raises(UploadValidationError, match="frame"):
        with prepare_upload(BytesIO(content.getvalue())):
            pytest.fail("Animation accepted")


@pytest.mark.parametrize(
    "limits", [UploadLimits(max_pixels=400), UploadLimits(max_dimension=90)]
)
def test_rejects_excessive_geometry(limits: UploadLimits) -> None:
    with pytest.raises(UploadValidationError, match="pixel limit"):
        with prepare_upload(BytesIO(image_bytes()), limits=limits):
            pytest.fail("Excessive geometry accepted")


def test_webp_geometry_check_precedes_decoder(monkeypatch: pytest.MonkeyPatch) -> None:
    original = image_bytes("WEBP")

    def forbidden(*args: object, **kwargs: object) -> None:
        pytest.fail("WebP decoder must not see excessive canvas")

    monkeypatch.setattr(Image, "open", forbidden)
    with pytest.raises(UploadValidationError, match="pixel limit"):
        with prepare_upload(BytesIO(original), limits=UploadLimits(max_pixels=400)):
            pytest.fail("Excessive geometry accepted")


def test_spools_to_disk_and_closes_on_consumer_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    streams = []
    factory = upload_images.SpooledTemporaryFile

    def tracked(max_size: int, mode: Literal["w+b"]) -> BinaryIO:
        stream = factory(max_size=max_size, mode=mode)
        streams.append(stream)
        return cast(BinaryIO, stream)

    monkeypatch.setattr(upload_images, "SpooledTemporaryFile", tracked)
    prepared = None
    with pytest.raises(RuntimeError, match="consumer"):
        with prepare_upload(
            BytesIO(image_bytes()), limits=UploadLimits(spool_memory_bytes=10)
        ) as prepared:
            assert getattr(streams[0], "_rolled", False)
            raise RuntimeError("consumer")
    assert streams[0].closed
    assert prepared is not None
    assert prepared.display.content.closed


def test_decode_concurrency_is_bounded_and_slot_released_after_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MEDIA_UPLOAD_DECODE_SLOTS", "1")
    upload_images._decoder_slots.cache_clear()
    original = image_bytes()
    try:
        with pytest.raises(RuntimeError, match="consumer failed"):
            with prepare_upload(BytesIO(original)):
                with pytest.raises(UploadBusyError):
                    with prepare_upload(BytesIO(original)):
                        pytest.fail("Concurrent decoder should be rejected")
                raise RuntimeError("consumer failed")
        with prepare_upload(BytesIO(original)) as prepared:
            assert prepared.original.content.read() == original
    finally:
        upload_images._decoder_slots.cache_clear()


@pytest.mark.parametrize("count", ["0", "3", "-1", "invalid"])
def test_decode_concurrency_configuration_is_bounded(
    monkeypatch: pytest.MonkeyPatch, count: str
) -> None:
    monkeypatch.setenv("MEDIA_UPLOAD_DECODE_SLOTS", count)
    upload_images._decoder_slots.cache_clear()
    try:
        with pytest.raises(ValueError):
            with prepare_upload(BytesIO(image_bytes())):
                pytest.fail("Invalid decoder count accepted")
    finally:
        upload_images._decoder_slots.cache_clear()


@pytest.mark.parametrize("value", [0, -1, True, 1.5])
def test_invalid_limits_rejected(value: int) -> None:
    with pytest.raises(ValueError):
        UploadLimits(max_bytes=value)
