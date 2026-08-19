from typing import cast

import pytest

from ebl.media.domain import (
    MediaAssociation,
    MediaId,
    MediaImportSource,
    MediaReference,
    MediaRepresentation,
    MediaRepresentations,
    MediaType,
    ThumbnailSize,
)
from ebl.tests.media.factories import (
    contract_media,
    original_representation,
    thumbnail_representation,
)
from ebl.transliteration.domain.museum_number import MuseumNumber

K1 = MuseumNumber.of("K.1")
PHOTO_ID = MediaId("550e8400-e29b-41d4-a716-446655440000")
CANONICAL_UUID = "550e8400-e29b-41d4-a716-446655440000"
BLANK_VALUES = ("", " ", "\t", "\n", "   ")


def representations_with(thumbnails: object) -> MediaRepresentations:
    return MediaRepresentations(original_representation(), cast(list, thumbnails))


@pytest.mark.parametrize(
    "thumbnails",
    [
        [("small", thumbnail_representation())],
        [(0, thumbnail_representation())],
        [(ThumbnailSize.SMALL, "not-a-representation")],
        [(ThumbnailSize.SMALL, thumbnail_representation(), "extra")],
        ["ab", "cd"],
        [ThumbnailSize.SMALL],
        [[ThumbnailSize.SMALL, thumbnail_representation()]],
    ],
)
def test_malformed_thumbnail_entries_are_rejected(thumbnails: object) -> None:
    with pytest.raises(ValueError):
        representations_with(thumbnails)


@pytest.mark.parametrize("size", tuple(ThumbnailSize))
def test_every_thumbnail_size_member_is_accepted(size: ThumbnailSize) -> None:
    result = representations_with([(size, thumbnail_representation())])

    assert result.thumbnails[0][0] is size


def test_duplicate_thumbnail_sizes_are_rejected() -> None:
    with pytest.raises(ValueError, match="duplicate thumbnail sizes"):
        representations_with(
            [
                (ThumbnailSize.SMALL, thumbnail_representation()),
                (ThumbnailSize.SMALL, thumbnail_representation("image/png")),
            ]
        )


def test_a_media_aggregate_cannot_hold_a_string_thumbnail_key() -> None:
    with pytest.raises(ValueError, match="ThumbnailSize member"):
        representations_with([("small", thumbnail_representation())])


@pytest.mark.parametrize("value", (True, False, 1.5, "1", None))
def test_representation_dimensions_reject_non_integers(value: object) -> None:
    with pytest.raises(ValueError, match="must be an integer"):
        MediaRepresentation("image/jpeg", cast(int, value), 3000, 100)


@pytest.mark.parametrize("value", (True, False, 1.5, "1", None))
def test_representation_file_size_rejects_non_integers(value: object) -> None:
    with pytest.raises(ValueError, match="must be an integer"):
        MediaRepresentation("image/jpeg", 4000, 3000, cast(int, value))


@pytest.mark.parametrize("value", (True, False, 1.5, "0", None))
def test_sort_order_rejects_non_integers(value: object) -> None:
    with pytest.raises(ValueError, match="must be an integer"):
        MediaAssociation(K1, cast(int, value))


@pytest.mark.parametrize("value", (0, 1, 2, 1000000))
def test_sort_order_accepts_non_negative_integers(value: int) -> None:
    assert MediaAssociation(K1, value).sort_order == value


def test_negative_sort_order_is_rejected() -> None:
    with pytest.raises(ValueError, match="cannot be negative"):
        MediaAssociation(K1, -1)


@pytest.mark.parametrize("value", ("yes", 1, 0, None))
def test_is_primary_rejects_non_booleans(value: object) -> None:
    with pytest.raises(ValueError, match="must be a boolean"):
        MediaAssociation(K1, 0, cast(bool, value))


@pytest.mark.parametrize("value", (True, False))
def test_is_primary_accepts_booleans(value: bool) -> None:
    assert MediaAssociation(K1, 0, value).is_primary is value


@pytest.mark.parametrize("value", BLANK_VALUES)
def test_blank_bibliography_id_is_rejected(value: str) -> None:
    with pytest.raises(ValueError, match="cannot be blank"):
        MediaReference(value)


@pytest.mark.parametrize("value", BLANK_VALUES)
def test_blank_import_source_fields_are_rejected(value: str) -> None:
    with pytest.raises(ValueError, match="cannot be blank"):
        MediaImportSource(value, "file-id")
    with pytest.raises(ValueError, match="cannot be blank"):
        MediaImportSource("legacy-gridfs", value)
    with pytest.raises(ValueError, match="cannot be blank"):
        MediaImportSource("legacy-gridfs", "file-id", container=value)


@pytest.mark.parametrize("value", BLANK_VALUES)
def test_blank_original_filename_is_rejected(value: str) -> None:
    with pytest.raises(ValueError, match="cannot be blank"):
        contract_media(
            PHOTO_ID,
            MediaType.PHOTO,
            (MediaAssociation(K1, 0, True),),
            original_filename=value,
        )


def test_import_source_container_is_optional_for_sources_without_one() -> None:
    source = MediaImportSource("local-archive", "scan-0001")

    assert source.container is None
    assert source.system == "local-archive"
    assert source.file_id == "scan-0001"


def test_canonical_media_id_is_accepted() -> None:
    assert str(MediaId(CANONICAL_UUID)) == CANONICAL_UUID


@pytest.mark.parametrize(
    "value",
    [
        "550E8400-E29B-41D4-A716-446655440000",
        "{550e8400-e29b-41d4-a716-446655440000}",
        "urn:uuid:550e8400-e29b-41d4-a716-446655440000",
        "550e8400e29b41d4a716446655440000",
        f" {CANONICAL_UUID} ",
        f"{CANONICAL_UUID}\n",
    ],
)
def test_non_canonical_uuid_spellings_are_rejected(value: str) -> None:
    with pytest.raises(ValueError):
        MediaId(value)


@pytest.mark.parametrize("value", (123, True, 1.5, None, b"bytes"))
def test_non_string_media_id_raises_value_error(value: object) -> None:
    with pytest.raises(ValueError, match="must be a string"):
        MediaId(cast(str, value))


def test_created_media_ids_are_canonical() -> None:
    created = MediaId.create()

    assert MediaId(str(created)) == created


def test_media_type_must_be_a_media_type_member() -> None:
    with pytest.raises(TypeError):
        contract_media(
            PHOTO_ID, cast(MediaType, "PHOTO"), (MediaAssociation(K1, 0, True),)
        )
