import pytest

from ebl.common.domain.project import ResearchProject
from ebl.media.domain import (
    Media,
    MediaAssociation,
    MediaChecksum,
    MediaId,
    MediaImportSource,
    MediaReference,
    MediaRepresentation,
    MediaRepresentations,
    MediaType,
    ThumbnailSize,
)


MEDIA_ID = "550e8400-e29b-41d4-a716-446655440000"
SHA256_VALUE = "a" * 64


def checksum() -> MediaChecksum:
    return MediaChecksum(value=SHA256_VALUE)


def original(mime_type: str = "image/jpeg") -> MediaRepresentation:
    return MediaRepresentation(mime_type, 4000, 3000, 5242880, checksum())


def thumbnails():
    return (
        (ThumbnailSize.SMALL, MediaRepresentation("image/jpeg", 240, 180, 15360)),
    )


def representations(mime_type: str = "image/jpeg") -> MediaRepresentations:
    return MediaRepresentations(original(mime_type), thumbnails())


def media(
    media_type: MediaType = MediaType.PHOTO,
    media_representations: MediaRepresentations = representations(),
    associations=(MediaAssociation("K.1", 0, True),),
    projects=(),
    references=(),
    import_source=None,
) -> Media:
    return Media(
        id=MEDIA_ID,
        type=media_type,
        original_filename="BM-12345-obverse.jpg",
        representations=media_representations,
        associations=associations,
        projects=projects,
        references=references,
        caption=None,
        attribution=None,
        import_source=import_source,
    )


def test_valid_photo() -> None:
    result = media(projects=(ResearchProject.CAIC,), references=(MediaReference("bib-id"),))

    assert result.id == MediaId(MEDIA_ID)
    assert result.type is MediaType.PHOTO
    assert result.projects == (ResearchProject.CAIC,)
    assert result.references == (MediaReference("bib-id"),)
    assert result.association_for("K.1").is_primary is True


def test_valid_raster_copy() -> None:
    result = media(MediaType.COPY)

    assert result.type is MediaType.COPY
    assert result.representations.original.mime_type == "image/jpeg"


def test_valid_svg_copy_metadata() -> None:
    result = media(MediaType.COPY, representations("image/svg+xml"))

    assert result.representations.original.mime_type == "image/svg+xml"


def test_svg_photo_is_invalid() -> None:
    with pytest.raises(ValueError, match="SVG originals"):
        media(MediaType.PHOTO, representations("image/svg+xml"))


def test_duplicate_associations_are_invalid() -> None:
    with pytest.raises(ValueError, match="duplicate fragment associations"):
        media(
            associations=(
                MediaAssociation("K.1", 0, True),
                MediaAssociation("K.1", 1, False),
            )
        )


def test_negative_sort_order_is_invalid() -> None:
    with pytest.raises(ValueError, match="sort_order"):
        MediaAssociation("K.1", -1)


def test_invalid_fragment_id_is_invalid() -> None:
    with pytest.raises(ValueError, match="valid museum number"):
        MediaAssociation("K-1", 0)


def test_invalid_uuid_is_invalid() -> None:
    with pytest.raises(ValueError, match="valid UUID"):
        MediaId("not-a-uuid")


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
        MediaRepresentations(None)


def test_missing_original_checksum_is_invalid() -> None:
    with pytest.raises(ValueError, match="checksum"):
        MediaRepresentations(MediaRepresentation("image/jpeg", 4000, 3000, 5242880))


def test_optional_legacy_metadata_can_be_empty() -> None:
    result = media()

    assert result.projects == ()
    assert result.references == ()
    assert result.caption is None
    assert result.attribution is None
    assert result.import_source is None


def test_import_source_metadata_can_be_recorded_without_defining_identity() -> None:
    import_source = MediaImportSource("legacy-gridfs", "photos", "legacy-gridfs-id")

    result = media(import_source=import_source)

    assert result.id == MediaId(MEDIA_ID)
    assert result.import_source == import_source


def test_associations_are_ordered_deterministically() -> None:
    result = media(
        associations=(
            MediaAssociation("Sm.2", 1, False),
            MediaAssociation("K.2", 0, False),
            MediaAssociation("K.1", 0, True),
        )
    )

    assert [str(association.fragment_id) for association in result.associations] == [
        "K.1",
        "K.2",
        "Sm.2",
    ]
