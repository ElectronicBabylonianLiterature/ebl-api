from io import BytesIO
from typing import Any, cast

import pytest

from ebl.media.application import (
    BackfillRequest,
    DisplayRepresentationWriteRequest,
    ImportMode,
    ImportRequest,
    MediaRepresentationNotFoundError,
    OriginalRepresentationWriteRequest,
    StoredRepresentationHandle,
    StoredRepresentationNotFoundError,
    ThumbnailRepresentationWriteRequest,
)
from ebl.media.domain import MediaAssociation, MediaId, MediaType, ThumbnailSize
from ebl.tests.media.factories import (
    association,
    contract_media,
    media_id,
    original_representation,
    photo_media,
)
from ebl.tests.media.in_memory_media import (
    InMemoryMediaRepository,
    InMemoryRepresentationStore,
)
from ebl.transliteration.domain.museum_number import MuseumNumber

PHOTO_ID = MediaId("550e8400-e29b-41d4-a716-446655440000")
K1 = MuseumNumber.of("K.1")


def write_content():
    return BytesIO(b"media-bytes")


def photo_with_small_thumbnail():
    return photo_media(media_id_=PHOTO_ID, associations=(association(fragment_id=K1),))


def make_request(request_type: Any, **kwargs: Any) -> Any:
    return request_type(**kwargs)


def test_original_write_request_cannot_carry_thumbnail_size() -> None:
    with pytest.raises(TypeError):
        make_request(
            OriginalRepresentationWriteRequest,
            media_id=media_id(),
            content=write_content(),
            representation=original_representation(),
            thumbnail_size=ThumbnailSize.SMALL,
        )


def test_display_write_request_cannot_carry_thumbnail_size() -> None:
    with pytest.raises(TypeError):
        make_request(
            DisplayRepresentationWriteRequest,
            media_id=media_id(),
            content=write_content(),
            representation=original_representation(),
            thumbnail_size=ThumbnailSize.SMALL,
        )


def test_thumbnail_write_request_requires_thumbnail_size() -> None:
    with pytest.raises(TypeError):
        make_request(
            ThumbnailRepresentationWriteRequest,
            media_id=media_id(),
            content=write_content(),
            representation=original_representation(),
        )


def test_thumbnail_write_request_rejects_invalid_thumbnail_size() -> None:
    with pytest.raises(TypeError):
        ThumbnailRepresentationWriteRequest(
            media_id(),
            write_content(),
            original_representation(),
            cast(ThumbnailSize, None),
        )


def test_representation_store_writes_accept_operation_specific_requests() -> None:
    original_request = OriginalRepresentationWriteRequest(
        media_id(), write_content(), original_representation()
    )
    display_request = DisplayRepresentationWriteRequest(
        media_id(), write_content(), original_representation()
    )
    thumbnail_request = ThumbnailRepresentationWriteRequest(
        media_id(), write_content(), original_representation(), ThumbnailSize.SMALL
    )
    store = InMemoryRepresentationStore()

    original_handle = store.write_original(original_request)
    display_handle = store.write_display(display_request)
    thumbnail_handle = store.write_thumbnail(thumbnail_request)

    assert store.written_originals == [original_request]
    assert store.written_displays == [display_request]
    assert store.written_thumbnails == [thumbnail_request]
    assert original_handle != display_handle
    assert display_handle != thumbnail_handle


def test_representation_open_returns_a_streamable_handle() -> None:
    request = OriginalRepresentationWriteRequest(
        PHOTO_ID, write_content(), original_representation()
    )
    store = InMemoryRepresentationStore()

    stored_handle = store.write_original(request)
    handle = store.open_representation(stored_handle)

    assert handle.media_id == PHOTO_ID
    assert handle.content_type == "image/jpeg"
    assert handle.content.read() == b"media-bytes"


def test_opening_an_absent_handle_raises_representation_not_found() -> None:
    store = InMemoryRepresentationStore()

    with pytest.raises(StoredRepresentationNotFoundError, match="missing"):
        store.open_representation(StoredRepresentationHandle("missing"))


def test_missing_role_error_identifies_media_and_representation() -> None:
    error = MediaRepresentationNotFoundError(PHOTO_ID, "display")

    assert error.media_id == PHOTO_ID
    assert error.representation == "display"
    assert str(error) == f"Media {PHOTO_ID} has no display representation."


def test_missing_thumbnail_error_names_thumbnail_size() -> None:
    error = MediaRepresentationNotFoundError.thumbnail(PHOTO_ID, ThumbnailSize.LARGE)

    assert error.representation == "large thumbnail"


def test_dry_run_import_request_carries_no_write_intent() -> None:
    request = ImportRequest(ImportMode.DRY_RUN, "legacy-gridfs", (K1,))
    repository = InMemoryMediaRepository(
        (contract_media(PHOTO_ID, MediaType.PHOTO, (MediaAssociation(K1, 0, True),)),)
    )
    store = InMemoryRepresentationStore()

    assert request.mode is ImportMode.DRY_RUN
    assert repository.find_by_fragment(K1) != ()
    assert store.written_originals == []
    assert store.written_thumbnails == []
    assert store.deleted_media_ids == []


def test_backfill_request_defaults_to_dry_run() -> None:
    request = BackfillRequest()

    assert request.dry_run is True
    assert request.batch_size is None
    assert request.resume_after is None


def test_backfill_request_supports_bounded_resumable_batches() -> None:
    request = BackfillRequest(dry_run=False, batch_size=100, resume_after="cursor-1")

    assert (request.dry_run, request.batch_size, request.resume_after) == (
        False,
        100,
        "cursor-1",
    )
