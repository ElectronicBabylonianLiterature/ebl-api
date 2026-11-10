import hashlib
import struct
import zlib
from io import BytesIO
from typing import BinaryIO, Literal, cast
from zlib import crc32

import pytest
from PIL import Image
from pymongo.database import Database

from ebl.media.application.media_stored import DisplayRepresentationWriteRequest
from ebl.media.application.media_storage_identity import StoredRepresentationHandle
from ebl.media.domain import MediaId, ThumbnailSize
from ebl.media.infrastructure import upload_images
from ebl.media.infrastructure.grid_fs_media_representation_store import (
    GridFsMediaRepresentationStore,
)
from ebl.media.infrastructure.upload_images import (
    UploadBusyError,
    UploadLimits,
    UploadTooLargeError,
    UploadValidationError,
    prepare_upload,
)
from ebl.tests.media.in_memory_representation_store import InMemoryRepresentationStore


def image_bytes(format: str = "PNG", size: tuple[int, int] = (96, 48)) -> bytes:
    with BytesIO() as content, Image.new("RGB", size, "red") as image:
        image.save(content, format=format)
        return content.getvalue()


@pytest.mark.parametrize(
    "format,mime",
    [("JPEG", "image/jpeg"), ("PNG", "image/png"), ("WEBP", "image/webp")],
)
def test_preserves_original_and_generates_all_derivatives(
    format: str, mime: str
) -> None:
    original = image_bytes(format, (1440, 720))
    with prepare_upload(
        BytesIO(original), content_length=len(original), declared_mime_type=mime
    ) as prepared:
        assert prepared.original.content.read() == original
        original_checksum = prepared.original.representation.checksum
        assert original_checksum is not None
        assert original_checksum.value == hashlib.sha256(original).hexdigest()
        assert prepared.original.representation.mime_type == mime
        assert prepared.original.representation.width == 1440
        assert prepared.display.representation.width == 1440
        assert [
            (size, item.representation.width, item.representation.height)
            for size, item in prepared.thumbnails
        ] == [
            (ThumbnailSize.SMALL, 240, 120),
            (ThumbnailSize.MEDIUM, 480, 240),
            (ThumbnailSize.LARGE, 720, 360),
        ]
        streams = [prepared.original.content, prepared.display.content] + [
            item.content for _, item in prepared.thumbnails
        ]
        for item in [prepared.display] + [item for _, item in prepared.thumbnails]:
            content = item.content.read()
            assert item.representation.mime_type == "image/jpeg"
            derivative_checksum = item.representation.checksum
            assert derivative_checksum is not None
            assert hashlib.sha256(content).hexdigest() == derivative_checksum.value
            with Image.open(BytesIO(content)) as decoded:
                decoded.load()
                assert decoded.size == (
                    item.representation.width,
                    item.representation.height,
                )
    assert all(stream.closed for stream in streams)


def test_exif_orientation_changes_only_derivatives() -> None:
    output = BytesIO()
    with Image.new("RGB", (80, 40), "red") as image:
        exif = Image.Exif()
        exif[274] = 6
        exif[315] = "Original photographer evidence"
        image.save(output, format="JPEG", exif=exif)
    original = output.getvalue()
    with prepare_upload(BytesIO(original)) as prepared:
        assert prepared.original.content.read() == original
        assert (
            prepared.original.representation.width,
            prepared.original.representation.height,
        ) == (80, 40)
        assert (
            prepared.display.representation.width,
            prepared.display.representation.height,
        ) == (40, 80)
        with Image.open(prepared.original.content) as image:
            assert image.getexif()[315] == "Original photographer evidence"
        with Image.open(prepared.display.content) as image:
            assert image.getexif().get(274, 1) == 1


def test_display_bounded_without_upscaling() -> None:
    with prepare_upload(BytesIO(image_bytes(size=(3000, 1000)))) as prepared:
        assert (
            prepared.display.representation.width,
            prepared.display.representation.height,
        ) == (2560, 853)


@pytest.mark.parametrize("format", ["JPEG", "PNG", "WEBP"])
def test_rejects_truncated_content(format: str) -> None:
    original = image_bytes(format)
    with pytest.raises(UploadValidationError):
        with prepare_upload(BytesIO(original[: len(original) // 2])):
            pytest.fail("Truncated image accepted")


@pytest.mark.parametrize(
    "content",
    [
        b"",
        b"not an image",
        b'<svg xmlns="http://www.w3.org/2000/svg"/>',
        b"GIF89a" + b"\x00" * 100,
    ],
)
def test_rejects_invalid_or_unsupported_content(content: bytes) -> None:
    with pytest.raises(UploadValidationError):
        with prepare_upload(BytesIO(content)):
            pytest.fail("Unsupported image accepted")


def test_rejects_browser_mime_mismatch() -> None:
    with pytest.raises(UploadValidationError, match="Content-Type"):
        with prepare_upload(BytesIO(image_bytes()), declared_mime_type="image/jpeg"):
            pytest.fail("Spoofed type accepted")


def test_rejects_png_with_valid_crc_but_corrupt_compressed_pixels() -> None:
    content = bytearray(image_bytes())
    offset = content.index(b"IDAT")
    length = int.from_bytes(content[offset - 4 : offset], "big")
    content[offset + 4] ^= 255
    checksum_offset = offset + 4 + length
    content[checksum_offset : checksum_offset + 4] = crc32(
        bytes(content[offset:checksum_offset])
    ).to_bytes(4, "big")
    # Container validation succeeds: full pixel decoding must still reject it.
    with Image.open(BytesIO(bytes(content))) as image:
        image.verify()
    with pytest.raises(UploadValidationError):
        with prepare_upload(BytesIO(bytes(content))):
            pytest.fail("Corrupt compressed pixels accepted")


def sixteen_bit_greyscale_png(width: int, height: int, sample: int) -> bytes:
    def chunk(kind: bytes, data: bytes) -> bytes:
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", crc32(body))

    row = b"\x00" + struct.pack(">H", sample) * width
    header = struct.pack(">IIBBBBB", width, height, 16, 0, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(row * height))
        + chunk(b"IEND", b"")
    )


@pytest.mark.parametrize("sample,expected", [(0, 0), (32768, 128), (65535, 255)])
# The wider original also exercises resizing to the display bound.
@pytest.mark.parametrize("width", [200, 3000])
def test_sixteen_bit_greyscale_previews_keep_tone(
    sample: int, expected: int, width: int
) -> None:
    content = BytesIO(sixteen_bit_greyscale_png(width, 40, sample))
    with Image.open(BytesIO(content.getvalue())) as decoded:
        assert decoded.mode == "I;16"
    with prepare_upload(BytesIO(content.getvalue())) as prepared:
        assert prepared.display.representation.width == min(width, 2560)
        for item in [prepared.display] + [item for _, item in prepared.thumbnails]:
            with Image.open(item.content) as preview:
                red, green, blue = preview.convert("RGB").getpixel(
                    (preview.width // 2, preview.height // 2)
                )
                assert red == green == blue
                assert abs(red - expected) <= 2


ByteOrder = Literal["big", "little"]


def exif_entry_offset(content: bytes, tag: int) -> tuple[int, ByteOrder]:
    tiff = content.index(b"Exif\x00\x00") + 6
    order: ByteOrder = "big" if content[tiff : tiff + 2] == b"MM" else "little"
    ifd = tiff + int.from_bytes(content[tiff + 4 : tiff + 8], order)
    for index in range(int.from_bytes(content[ifd : ifd + 2], order)):
        entry = ifd + 2 + 12 * index
        if int.from_bytes(content[entry : entry + 2], order) == tag:
            return entry, order
    raise AssertionError(f"EXIF tag {tag} not written")


def test_rejects_malformed_exif_as_invalid_content() -> None:
    output = BytesIO()
    with Image.new("RGB", (80, 40), "red") as image:
        exif = Image.Exif()
        exif[274] = 6
        exif[282] = 72.0
        image.save(output, format="JPEG", exif=exif)
    content = bytearray(output.getvalue())
    # Retype XResolution from RATIONAL (5) to ASCII (2): orientation handling
    # then fails re-serialising EXIF with a non-OSError (TypeError).
    entry, order = exif_entry_offset(bytes(content), 282)
    content[entry + 2 : entry + 4] = (2).to_bytes(2, order)
    with pytest.raises(UploadValidationError, match="Invalid or unsafe") as error:
        with prepare_upload(BytesIO(bytes(content))):
            pytest.fail("Malformed EXIF accepted")
    assert error.value.__cause__ is not None


def test_memory_errors_are_not_reported_as_invalid_content(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def exhausted(image: Image.Image) -> Image.Image:
        raise MemoryError()

    monkeypatch.setattr(upload_images.ImageOps, "exif_transpose", exhausted)
    with pytest.raises(MemoryError):
        with prepare_upload(BytesIO(image_bytes())):
            pytest.fail("Exhausted decoder accepted")


@pytest.mark.parametrize("declared", [1, 100000])
def test_rejects_length_mismatch(declared: int) -> None:
    with pytest.raises(UploadValidationError, match="length"):
        with prepare_upload(BytesIO(image_bytes()), content_length=declared):
            pytest.fail("Mismatched length accepted")


def test_prechecks_declared_oversize_without_reading() -> None:
    class NoReads(BytesIO):
        def read(self, size: int = -1) -> bytes:
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

    def tracked(*args: object, **kwargs: object) -> BinaryIO:
        stream = factory(*args, **kwargs)
        streams.append(stream)
        return cast(BinaryIO, stream)

    monkeypatch.setattr(upload_images, "SpooledTemporaryFile", tracked)
    with pytest.raises(RuntimeError, match="consumer"):
        with prepare_upload(
            BytesIO(image_bytes()), limits=UploadLimits(spool_memory_bytes=10)
        ) as prepared:
            assert streams[0]._rolled
            raise RuntimeError("consumer")
    assert streams[0].closed
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


def test_stores_owned_handles_and_journals_each_write() -> None:
    store = InMemoryRepresentationStore()
    journal: list[StoredRepresentationHandle] = []
    original = image_bytes()
    with prepare_upload(BytesIO(original)) as prepared:
        handles = prepared.store(store, MediaId.create(), journal.append)
    assert len(journal) == 5
    assert len({handle.value for handle in journal}) == 5
    with store.open_representation(handles.original).content as content:
        assert content.read() == original


@pytest.mark.parametrize("format", ["JPEG", "PNG", "WEBP"])
def test_real_gridfs_owned_original_and_derivative_roundtrip(
    media_database: Database, format: str
) -> None:
    store = GridFsMediaRepresentationStore(media_database)
    store.create_indexes()
    original = image_bytes(format)
    journal: list[StoredRepresentationHandle] = []
    with prepare_upload(BytesIO(original)) as prepared:
        handles = prepared.store(store, MediaId.create(), journal.append)
    assert media_database["media.files"].count_documents({}) == 5
    assert media_database["photos.files"].count_documents({}) == 0
    assert len(journal) == 5
    with store.open_representation(handles.original).content as content:
        assert content.read() == original
    for handle in handles.handles:
        with store.open_representation(handle).content as content:
            value = content.read()
        stored_checksum = handle.representation.checksum
        assert stored_checksum is not None
        assert hashlib.sha256(value).hexdigest() == stored_checksum.value
        with Image.open(BytesIO(value)) as image:
            image.load()
            assert image.size == (
                handle.representation.width,
                handle.representation.height,
            )


def test_real_gridfs_failed_derivative_cleans_only_uncommitted_upload(
    media_database: Database,
) -> None:
    class FailingStore(GridFsMediaRepresentationStore):
        def write_display(
            self, request: DisplayRepresentationWriteRequest
        ) -> StoredRepresentationHandle:
            raise RuntimeError("interrupted display write")

    healthy = GridFsMediaRepresentationStore(media_database)
    healthy.create_indexes()
    with prepare_upload(BytesIO(image_bytes())) as prepared:
        previous = prepared.store(healthy, MediaId.create())
    with prepare_upload(BytesIO(image_bytes())) as prepared:
        with pytest.raises(RuntimeError, match="interrupted display write"):
            prepared.store(FailingStore(media_database), MediaId.create())
    assert media_database["media.files"].count_documents({}) == 5
    assert media_database["media.chunks"].count_documents({}) == 5
    assert media_database.mediaFiles.count_documents({"deleted": True}) == 1
    with healthy.open_representation(previous.original).content as content:
        assert content.read() == image_bytes()


def test_failed_store_cleans_only_current_upload_handles() -> None:
    class FailingStore(InMemoryRepresentationStore):
        def write_display(
            self, request: DisplayRepresentationWriteRequest
        ) -> StoredRepresentationHandle:
            raise RuntimeError("storage interrupted")

    store = FailingStore()
    journal: list[StoredRepresentationHandle] = []
    with prepare_upload(BytesIO(image_bytes())) as prepared:
        with pytest.raises(RuntimeError, match="storage interrupted"):
            prepared.store(store, MediaId.create(), journal.append)
    assert len(journal) == 1
    assert store.deleted_handles == journal
    assert not store.contains(journal[0])


def test_failed_journal_callback_cleans_staged_handle() -> None:
    store = InMemoryRepresentationStore()

    def failure(handle: StoredRepresentationHandle) -> None:
        raise RuntimeError("journal unavailable")

    with prepare_upload(BytesIO(image_bytes())) as prepared:
        with pytest.raises(RuntimeError, match="journal unavailable"):
            prepared.store(store, MediaId.create(), failure)
    assert len(store.deleted_handles) == 1


def test_cleanup_failure_keeps_primary_failure_and_registered_orphan(
    caplog: pytest.LogCaptureFixture,
) -> None:
    class FailingStore(InMemoryRepresentationStore):
        def write_display(
            self, request: DisplayRepresentationWriteRequest
        ) -> StoredRepresentationHandle:
            raise RuntimeError("storage interrupted")

        def delete_representation(self, handle: StoredRepresentationHandle) -> None:
            raise RuntimeError("cleanup interrupted")

    store = FailingStore()
    journal: list[StoredRepresentationHandle] = []
    with prepare_upload(BytesIO(image_bytes())) as prepared:
        with pytest.raises(RuntimeError, match="storage interrupted"):
            prepared.store(store, MediaId.create(), journal.append)
    assert store.contains(journal[0])
    assert "Upload staging cleanup failed" in caplog.text


@pytest.mark.parametrize("value", [0, -1, True, 1.5])
def test_invalid_limits_rejected(value: int) -> None:
    with pytest.raises(ValueError):
        UploadLimits(max_bytes=value)
