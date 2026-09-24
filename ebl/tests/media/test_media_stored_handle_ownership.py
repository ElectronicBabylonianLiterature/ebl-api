from io import BytesIO

import attr
import pytest

from ebl.media.application import (
    OriginalRepresentationWriteRequest,
    StoredMedia,
    StoredMediaRepresentations,
    StoredRepresentationHandle,
    StoredRepresentationMissingError,
    StoredRepresentationRole,
    StoredThumbnailRepresentation,
)
from ebl.media.domain import MediaId, ThumbnailSize
from ebl.tests.media.factories import (
    display_representation,
    original_representation,
    photo_media,
    representations,
)
from ebl.tests.media.in_memory_media import InMemoryRepresentationStore
from ebl.tests.media.representation_helpers import representation_for_content

FIRST_ID = MediaId("550e8400-e29b-41d4-a716-446655440000")
SECOND_ID = MediaId("550e8400-e29b-41d4-a716-446655440002")


def test_stored_media_rejects_a_handle_owned_by_another_media() -> None:
    media = photo_media(media_id_=FIRST_ID)
    foreign_handle = StoredRepresentationHandle(
        SECOND_ID, "foreign-original", media.representations.original
    )

    with pytest.raises(ValueError, match="handles must belong to the media"):
        StoredMedia(media, StoredMediaRepresentations(foreign_handle))


def test_stored_handle_identity_includes_its_owner() -> None:
    representation = original_representation()
    first = StoredRepresentationHandle(FIRST_ID, "same-provider-key", representation)
    second = StoredRepresentationHandle(SECOND_ID, "same-provider-key", representation)

    assert first != second
    assert len({first, second}) == 2


def test_stored_media_rejects_a_handle_for_the_wrong_role() -> None:
    media = photo_media(media_id_=FIRST_ID)
    display_handle = StoredRepresentationHandle(
        FIRST_ID,
        "display",
        media.representations.original,
        role=StoredRepresentationRole.DISPLAY,
    )

    with pytest.raises(ValueError, match="original role"):
        StoredMedia(media, StoredMediaRepresentations(display_handle))


def test_stored_media_rejects_a_handle_for_another_metadata_version() -> None:
    media = photo_media(media_id_=FIRST_ID)
    wrong_version = attr.evolve(
        media.representations.original,
        file_size=media.representations.original.file_size + 1,
    )
    stale_handle = StoredRepresentationHandle(FIRST_ID, "stale-original", wrong_version)

    with pytest.raises(ValueError, match="original role and metadata"):
        StoredMedia(media, StoredMediaRepresentations(stale_handle))


def test_stored_media_rejects_a_display_handle_for_the_wrong_role() -> None:
    media = photo_media(
        media_id_=FIRST_ID,
        media_representations=representations(display=display_representation()),
    )
    display = media.representations.display
    assert display is not None

    with pytest.raises(ValueError, match="display role"):
        StoredMedia(
            media,
            StoredMediaRepresentations(
                StoredRepresentationHandle(
                    FIRST_ID, "original", media.representations.original
                ),
                display=StoredRepresentationHandle(
                    FIRST_ID,
                    "display",
                    display,
                ),
            ),
        )


def test_stored_media_rejects_a_thumbnail_handle_for_the_wrong_role() -> None:
    media = photo_media(media_id_=FIRST_ID)

    with pytest.raises(ValueError, match="thumbnail role"):
        StoredMedia(
            media,
            StoredMediaRepresentations(
                StoredRepresentationHandle(
                    FIRST_ID, "original", media.representations.original
                ),
                (
                    StoredThumbnailRepresentation(
                        ThumbnailSize.SMALL,
                        StoredRepresentationHandle(
                            FIRST_ID,
                            "small",
                            dict(media.representations.thumbnails)[ThumbnailSize.SMALL],
                        ),
                    ),
                ),
            ),
        )


@pytest.mark.parametrize(
    "role,thumbnail_size",
    (
        (StoredRepresentationRole.THUMBNAIL, None),
        (StoredRepresentationRole.ORIGINAL, ThumbnailSize.SMALL),
    ),
)
def test_stored_handle_role_and_thumbnail_size_must_agree(
    role: StoredRepresentationRole, thumbnail_size: ThumbnailSize | None
) -> None:
    with pytest.raises(ValueError, match="Only thumbnail handles"):
        StoredRepresentationHandle(
            FIRST_ID,
            "invalid",
            original_representation(),
            role=role,
            thumbnail_size=thumbnail_size,
        )


def test_store_does_not_open_a_handle_forged_for_another_owner() -> None:
    content = b"owner-bound"
    representation = representation_for_content(content, original_representation())
    store = InMemoryRepresentationStore()
    stored = store.write_original(
        OriginalRepresentationWriteRequest(FIRST_ID, BytesIO(content), representation)
    )
    forged = StoredRepresentationHandle(SECOND_ID, stored.value, stored.representation)

    with pytest.raises(StoredRepresentationMissingError):
        store.open_representation(forged)
