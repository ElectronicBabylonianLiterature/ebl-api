from typing import cast
from uuid import UUID

import attr
import pytest

from ebl.common.domain.project import ResearchProject
from ebl.media.domain import (
    MediaAssociation,
    MediaChecksum,
    MediaId,
    MediaRepresentation,
    MediaRepresentations,
    MediaType,
    ThumbnailSize,
)
from ebl.tests.media.factories import (
    DEFAULT_MEDIA_ID,
    SHA256_VALUE,
    association,
    copy_media,
    display_representation,
    media_import_source,
    media_reference,
    original_representation,
    photo_media,
    representations,
    thumbnail_representation,
)
from ebl.transliteration.domain.museum_number import MuseumNumber


def test_valid_photo() -> None:
    result = photo_media(
        projects=(ResearchProject.CAIC,),
        references=(media_reference("bib-id"),),
    )

    assert result.id == MediaId(DEFAULT_MEDIA_ID)
    assert result.type is MediaType.PHOTO
    assert result.projects == (ResearchProject.CAIC,)
    assert result.references == (media_reference("bib-id"),)
    assert result.association_for("K.1").is_primary is True


def test_valid_raster_copy() -> None:
    result = copy_media()

    assert result.type is MediaType.COPY
    assert result.representations.original.mime_type == "image/jpeg"
    assert result.representations.display is None


def test_valid_photo_with_display_representation() -> None:
    result = photo_media(
        media_representations=representations(display_mime_type="image/jpeg")
    )

    assert result.representations.display == display_representation()


def test_valid_photo_with_display_and_thumbnails() -> None:
    result = photo_media(
        media_representations=representations(display_mime_type="image/webp")
    )

    assert result.representations.display == display_representation("image/webp")
    assert result.representations.thumbnails == (
        (ThumbnailSize.SMALL, thumbnail_representation()),
    )


def test_valid_svg_copy_metadata() -> None:
    result = copy_media(
        media_representations=representations(
            original_mime_type="image/svg+xml", display_mime_type="image/jpeg"
        )
    )

    assert result.representations.original.mime_type == "image/svg+xml"
    assert result.representations.display == display_representation()


def test_svg_photo_is_invalid() -> None:
    with pytest.raises(ValueError, match="SVG originals"):
        photo_media(
            media_representations=representations(
                original_mime_type="image/svg+xml", display_mime_type="image/jpeg"
            )
        )


def test_duplicate_associations_are_invalid() -> None:
    with pytest.raises(ValueError, match="duplicate fragment associations"):
        photo_media(
            associations=(
                MediaAssociation(MuseumNumber.of("K.1"), 0, True),
                MediaAssociation(MuseumNumber.of("K.1"), 1, False),
            )
        )


def test_empty_associations_are_invalid() -> None:
    with pytest.raises(ValueError, match="at least one item"):
        photo_media(associations=())


def test_negative_sort_order_is_invalid() -> None:
    with pytest.raises(ValueError, match="sort_order"):
        MediaAssociation(MuseumNumber.of("K.1"), -1)


def test_invalid_fragment_id_is_invalid() -> None:
    with pytest.raises(ValueError, match="valid museum number"):
        MediaAssociation(cast(MuseumNumber, "K-1"), 0)


def test_invalid_uuid_is_invalid() -> None:
    with pytest.raises(ValueError, match="valid UUID"):
        MediaId("not-a-uuid")


def test_empty_media_id_is_invalid() -> None:
    with pytest.raises(ValueError, match="cannot be empty"):
        MediaId("")


def test_media_id_create_returns_unique_uuid() -> None:
    first = MediaId.create()
    second = MediaId.create()

    assert UUID(str(first))
    assert UUID(str(second))
    assert first != second


@pytest.mark.parametrize(
    "algorithm,value",
    [
        ("md5", SHA256_VALUE),
        ("sha256", "not-hex"),
        ("sha256", "a" * 63),
    ],
)
def test_invalid_checksum_is_invalid(algorithm, value) -> None:
    with pytest.raises(ValueError):
        MediaChecksum(algorithm=algorithm, value=value)


@pytest.mark.parametrize(
    "width,height,file_size",
    [
        (0, 3000, 100),
        (4000, 0, 100),
        (4000, 3000, 0),
    ],
)
def test_invalid_representation_dimensions_or_file_size_are_invalid(
    width, height, file_size
) -> None:
    with pytest.raises(ValueError):
        MediaRepresentation("image/jpeg", width, height, file_size)


def test_missing_original_representation_is_invalid() -> None:
    with pytest.raises(ValueError, match="original representation"):
        MediaRepresentations(cast(MediaRepresentation, None))


def test_missing_original_checksum_is_invalid() -> None:
    with pytest.raises(ValueError, match="checksum"):
        MediaRepresentations(MediaRepresentation("image/jpeg", 4000, 3000, 5242880))


def test_duplicate_thumbnail_sizes_are_invalid() -> None:
    with pytest.raises(ValueError, match="duplicate thumbnail sizes"):
        MediaRepresentations(
            original_representation(),
            (
                (
                    ThumbnailSize.SMALL,
                    MediaRepresentation("image/jpeg", 240, 180, 15360),
                ),
                (
                    ThumbnailSize.SMALL,
                    MediaRepresentation("image/jpeg", 480, 360, 61440),
                ),
            ),
        )


def test_optional_legacy_metadata_can_be_empty() -> None:
    result = photo_media()

    assert result.projects == ()
    assert result.references == ()
    assert result.caption is None
    assert result.attribution is None
    assert result.import_source is None


def test_media_representations_are_immutable() -> None:
    field = "display"

    with pytest.raises(attr.exceptions.FrozenInstanceError):
        setattr(
            representations(display_mime_type="image/jpeg"),
            field,
            display_representation("image/webp"),
        )


def test_import_source_metadata_can_be_recorded_without_defining_identity() -> None:
    import_source = media_import_source()

    result = photo_media(import_source=import_source)

    assert result.id == MediaId(DEFAULT_MEDIA_ID)
    assert result.import_source == import_source


def test_is_associated_with_returns_false_for_unrelated_fragment() -> None:
    assert photo_media().is_associated_with("Sm.2") is False


def test_association_for_raises_for_unrelated_fragment() -> None:
    with pytest.raises(ValueError, match="not associated with fragment"):
        photo_media().association_for("Sm.2")


def test_associations_are_ordered_deterministically() -> None:
    result = photo_media(
        associations=(
            association(fragment_id="Sm.2", sort_order=1, is_primary=False),
            association(fragment_id="K.2", sort_order=0, is_primary=False),
            association(fragment_id="K.1", sort_order=0, is_primary=True),
        )
    )

    assert [str(association.fragment_id) for association in result.associations] == [
        "K.1",
        "K.2",
        "Sm.2",
    ]
