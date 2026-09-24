from collections.abc import Callable
from io import BytesIO

import pytest

from ebl.errors import NotFoundError
from ebl.media.application import (
    DisplayRepresentationWriteRequest,
    ImportMode,
    ImportRequest,
    MediaRepresentationNotFoundError,
    OriginalRepresentationWriteRequest,
    StoredRepresentationHandle,
    StoredRepresentationMissingError,
    ThumbnailRepresentationWriteRequest,
)
from ebl.media.domain import Media, MediaId, MediaRepresentation, ThumbnailSize
from ebl.tests.media.factories import (
    association,
    media_id,
    original_representation,
    photo_media,
)
from ebl.tests.media.in_memory_media import (
    InMemoryRepresentationStore,
)
from ebl.tests.media.representation_helpers import representation_for_content
from ebl.transliteration.domain.museum_number import MuseumNumber

PHOTO_ID = MediaId("550e8400-e29b-41d4-a716-446655440000")
K1 = MuseumNumber.of("K.1")
WRITE_CONTENT = b"media-bytes"


def write_content() -> BytesIO:
    return BytesIO(WRITE_CONTENT)


def write_representation() -> MediaRepresentation:
    return representation_for_content(WRITE_CONTENT, original_representation())


def photo_with_small_thumbnail() -> Media:
    return photo_media(media_id_=PHOTO_ID, associations=(association(fragment_id=K1),))


def make_request(request_type: Callable[..., object], **kwargs: object) -> object:
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


def test_representation_store_writes_accept_operation_specific_requests() -> None:
    original_request = OriginalRepresentationWriteRequest(
        media_id(), write_content(), write_representation()
    )
    display_request = DisplayRepresentationWriteRequest(
        media_id(), write_content(), write_representation()
    )
    thumbnail_request = ThumbnailRepresentationWriteRequest(
        media_id(), write_content(), write_representation(), ThumbnailSize.SMALL
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
        PHOTO_ID, write_content(), write_representation()
    )
    store = InMemoryRepresentationStore()

    stored_handle = store.write_original(request)
    handle = store.open_representation(stored_handle)

    assert handle.media_id == PHOTO_ID
    assert handle.representation.mime_type == "image/jpeg"
    assert handle.content.read() == WRITE_CONTENT


def test_deleted_handle_value_is_never_reissued() -> None:
    store = InMemoryRepresentationStore()
    first = store.write_original(
        OriginalRepresentationWriteRequest(
            PHOTO_ID, write_content(), write_representation()
        )
    )
    store.delete_representation(first)

    second = store.write_original(
        OriginalRepresentationWriteRequest(
            PHOTO_ID, write_content(), write_representation()
        )
    )

    assert second != first
    assert second.value != first.value


def test_opening_an_absent_handle_raises_a_storage_integrity_error() -> None:
    store = InMemoryRepresentationStore()
    handle = StoredRepresentationHandle(
        PHOTO_ID, "secret-gridfs-object-id", original_representation()
    )

    with pytest.raises(StoredRepresentationMissingError) as error_info:
        store.open_representation(handle)

    error = error_info.value
    assert error.handle == handle
    assert "secret-gridfs-object-id" not in str(error)
    assert str(error) == "Stored media representation not found."
    assert not isinstance(error, NotFoundError)


def test_missing_role_error_identifies_media_and_representation() -> None:
    error = MediaRepresentationNotFoundError(PHOTO_ID, "display")

    assert error.media_id == PHOTO_ID
    assert error.representation == "display"
    assert str(error) == f"Media {PHOTO_ID} has no display representation."


def test_missing_thumbnail_error_names_thumbnail_size() -> None:
    error = MediaRepresentationNotFoundError.thumbnail(PHOTO_ID, ThumbnailSize.LARGE)

    assert error.representation == "large thumbnail"


@pytest.mark.parametrize("mode", tuple(ImportMode))
def test_dry_run_is_orthogonal_to_the_import_mode(mode: ImportMode) -> None:
    preview = ImportRequest(mode, "legacy-gridfs", (K1,), dry_run=True)
    applied = ImportRequest(mode, "legacy-gridfs", (K1,))

    assert preview.mode is mode
    assert preview.dry_run is True
    assert applied.mode is mode
    assert applied.dry_run is False


def test_import_modes_describe_only_existing_source_handling() -> None:
    assert {mode.value for mode in ImportMode} == {"skip-existing", "replace"}


def test_import_request_collections_are_immutable() -> None:
    fragment_ids = [K1]
    request = ImportRequest(ImportMode.REPLACE, "legacy-gridfs", fragment_ids)

    fragment_ids.append(MuseumNumber.of("BM.99"))

    assert request.fragment_ids == (K1,)
