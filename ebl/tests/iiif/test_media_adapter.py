import pytest

from ebl.iiif.application.media_adapter import media_source_of
from ebl.media.domain import MediaRepresentations, ThumbnailSize
from ebl.tests.media.factories import (
    DEFAULT_MEDIA_ID,
    association,
    copy_media,
    large_thumbnail_representation,
    medium_thumbnail_representation,
    original_representation,
    photo_media,
    representations,
    thumbnail_representation,
)
from ebl.transliteration.domain.museum_number import MuseumNumber

NUMBER = MuseumNumber.of("K.1")
OTHER_NUMBER = MuseumNumber.of("K.2")


def test_media_source_maps_identity_ordering_and_primary_state() -> None:
    media = photo_media(
        associations=(association(sort_order=3, is_primary=True),),
    )

    source = media_source_of(NUMBER, media)

    assert source.media_id == DEFAULT_MEDIA_ID
    assert source.sort_order == 3
    assert source.is_primary is True


def test_media_source_maps_canvas_dimensions_from_original() -> None:
    source = media_source_of(NUMBER, photo_media())

    assert source.canvas_width == 4000
    assert source.canvas_height == 3000


def test_media_source_maps_caption_and_attribution() -> None:
    media = photo_media(caption="Obverse", attribution="The British Museum")

    source = media_source_of(NUMBER, media)

    assert source.label == "Obverse"
    assert source.attribution == "The British Museum"


def test_media_source_never_invents_rights_or_publication_state() -> None:
    source = media_source_of(NUMBER, photo_media(attribution="The British Museum"))

    assert source.rights is None
    assert source.is_public is False


def test_media_source_paints_the_original_when_no_display_exists() -> None:
    source = media_source_of(NUMBER, photo_media())

    painting_image = source.painting_image
    assert painting_image is not None
    assert painting_image.url == f"/fragments/K.1/media/{DEFAULT_MEDIA_ID}/file"
    assert painting_image.mime_type == "image/jpeg"
    assert painting_image.width == 4000
    assert painting_image.height == 3000


def test_media_source_prefers_the_display_representation_for_painting() -> None:
    media = photo_media(
        media_representations=representations(display_mime_type="image/jpeg")
    )

    source = media_source_of(NUMBER, media)

    painting_image = source.painting_image
    assert painting_image is not None
    assert painting_image.url == f"/fragments/K.1/media/{DEFAULT_MEDIA_ID}/display"
    assert painting_image.width == 2560


def test_media_source_has_no_painting_image_for_a_non_raster_original() -> None:
    media = copy_media(
        media_representations=MediaRepresentations(
            original_representation("image/svg+xml")
        )
    )

    source = media_source_of(NUMBER, media)

    assert source.painting_image is None


def test_media_source_maps_the_smallest_available_thumbnail() -> None:
    media = photo_media(
        media_representations=representations(
            thumbnails=(
                (ThumbnailSize.MEDIUM, medium_thumbnail_representation()),
                (ThumbnailSize.SMALL, thumbnail_representation()),
            )
        )
    )

    source = media_source_of(NUMBER, media)

    thumbnail_image = source.thumbnail_image
    assert thumbnail_image is not None
    assert thumbnail_image.url == (
        f"/fragments/K.1/media/{DEFAULT_MEDIA_ID}/thumbnail/small"
    )
    assert thumbnail_image.width == 240


def test_media_source_falls_back_to_a_larger_thumbnail() -> None:
    media = photo_media(
        media_representations=representations(
            thumbnails=((ThumbnailSize.LARGE, large_thumbnail_representation()),)
        )
    )

    source = media_source_of(NUMBER, media)

    thumbnail_image = source.thumbnail_image
    assert thumbnail_image is not None
    assert thumbnail_image.url == (
        f"/fragments/K.1/media/{DEFAULT_MEDIA_ID}/thumbnail/large"
    )


def test_media_source_has_no_thumbnail_when_none_are_stored() -> None:
    media = photo_media(
        media_representations=MediaRepresentations(original_representation())
    )

    source = media_source_of(NUMBER, media)

    assert source.thumbnail_image is None


def test_media_source_renders_a_non_paintable_original_as_a_rendering() -> None:
    media = copy_media(
        original_filename="BM-12345-copy.svg",
        media_representations=MediaRepresentations(
            original_representation("image/svg+xml")
        ),
    )

    source = media_source_of(NUMBER, media)

    rendering = source.rendering
    assert rendering is not None
    assert rendering.url == (
        "/fragments/K.1/media/550e8400-e29b-41d4-a716-446655440001/file"
    )
    assert rendering.mime_type == "image/svg+xml"
    assert rendering.label == "BM-12345-copy.svg"


def test_media_source_has_no_rendering_for_a_paintable_original() -> None:
    assert media_source_of(NUMBER, photo_media()).rendering is None


def test_media_source_rejects_an_unassociated_fragment() -> None:
    with pytest.raises(ValueError):
        media_source_of(OTHER_NUMBER, photo_media())
