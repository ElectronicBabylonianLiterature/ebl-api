from typing import Sequence, cast

import attr
import pytest

from ebl.media.domain import (
    MediaAssociation,
    MediaChecksum,
    MediaImportSource,
    MediaReference,
    MediaRepresentation,
    MediaRepresentations,
    ThumbnailSize,
)
from ebl.common.domain.project import ResearchProject
from ebl.tests.media.factories import original_representation, photo_media
from ebl.transliteration.domain.museum_number import MuseumNumber


@pytest.mark.parametrize("mime_type", (None, 1, b"image/jpeg"))
def test_representation_mime_type_rejects_non_strings(mime_type: object) -> None:
    with pytest.raises(ValueError, match="MIME type must be a string"):
        MediaRepresentation(cast(str, mime_type), 1, 1, 1)


def test_representation_rejects_a_non_checksum_value() -> None:
    with pytest.raises(ValueError, match="checksum must be a MediaChecksum"):
        MediaRepresentation(
            "image/jpeg", 1, 1, 1, cast(MediaChecksum, "not-a-checksum")
        )


def test_representations_reject_a_non_representation_original() -> None:
    with pytest.raises(ValueError, match="original representation"):
        MediaRepresentations(cast(MediaRepresentation, "not-a-representation"))


def test_representations_reject_a_non_representation_display() -> None:
    with pytest.raises(ValueError, match="display must be a MediaRepresentation"):
        MediaRepresentations(
            original_representation(),
            display=cast(MediaRepresentation, "not-a-representation"),
        )


def test_media_rejects_a_non_representations_value() -> None:
    with pytest.raises(ValueError, match="representations must be a"):
        photo_media(
            media_representations=cast(
                MediaRepresentations, "not-media-representations"
            )
        )


def test_media_rejects_a_non_association_member() -> None:
    with pytest.raises(ValueError, match="only MediaAssociation values"):
        photo_media(associations=(cast(MediaAssociation, "not-an-association"),))


def test_media_collection_converter_rejects_a_non_sequence() -> None:
    with pytest.raises(ValueError, match="must be a sequence"):
        attr.evolve(photo_media(), projects=cast(Sequence[ResearchProject], 1))


def test_media_associations_converter_rejects_a_non_sequence() -> None:
    with pytest.raises(ValueError, match="Associations must be a sequence"):
        photo_media(associations=cast(Sequence[MediaAssociation], 1))


def test_media_references_converter_rejects_a_non_sequence() -> None:
    with pytest.raises(ValueError, match="References must be a sequence"):
        attr.evolve(photo_media(), references=cast(Sequence[MediaReference], 1))


def test_thumbnails_converter_rejects_a_non_sequence() -> None:
    with pytest.raises(ValueError, match="Thumbnails must be a sequence"):
        MediaRepresentations(
            original_representation(),
            cast(Sequence[tuple[ThumbnailSize, MediaRepresentation]], 1),
        )


def test_media_collection_converter_rejects_a_bare_string() -> None:
    with pytest.raises(ValueError, match="sequence, not a string"):
        attr.evolve(photo_media(), projects=cast(Sequence[ResearchProject], "CAIC"))


def test_association_rejects_a_non_string_fragment_id() -> None:
    with pytest.raises(ValueError, match="string or MuseumNumber"):
        MediaAssociation(cast(MuseumNumber, 1), 0)


@pytest.mark.parametrize("field_name", ("caption", "attribution"))
def test_media_text_metadata_rejects_non_strings(field_name: str) -> None:
    with pytest.raises(ValueError, match=rf"{field_name} must be a str"):
        photo_media(**{field_name: 1})


def test_media_text_metadata_preserves_empty_strings() -> None:
    media = photo_media(caption="", attribution="")

    assert media.caption == ""
    assert media.attribution == ""


def test_media_rejects_a_non_import_source_value() -> None:
    with pytest.raises(ValueError, match="import_source must be a MediaImportSource"):
        photo_media(import_source=cast(MediaImportSource, "not-an-import-source"))


def test_valid_optional_domain_types_are_preserved() -> None:
    checksum = MediaChecksum(value="a" * 64)
    import_source = MediaImportSource("archive", "file-id")
    representation = MediaRepresentation("image/jpeg", 1, 1, 1, checksum)
    media = photo_media(import_source=import_source)

    assert representation.checksum is checksum
    assert media.import_source is import_source


def test_is_associated_with_returns_true_for_an_associated_fragment() -> None:
    assert photo_media().is_associated_with("K.1") is True
