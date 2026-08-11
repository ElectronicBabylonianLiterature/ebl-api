import pytest

from ebl.media.domain import MediaRepresentations, ThumbnailSize
from ebl.tests.media.factories import (
    copy_media,
    display_representation,
    original_representation,
    photo_media,
    representations,
    thumbnail_representation,
)

SVG = "image/svg+xml"


def test_svg_original_is_valid_for_copy() -> None:
    result = copy_media(
        media_representations=representations(
            original_mime_type=SVG, display_mime_type="image/jpeg"
        )
    )

    assert result.representations.original.mime_type == SVG


def test_svg_display_is_rejected_for_copy() -> None:
    with pytest.raises(ValueError, match="SVG representations"):
        copy_media(media_representations=representations(display_mime_type=SVG))


def test_svg_original_is_rejected_for_photo() -> None:
    with pytest.raises(ValueError, match="SVG representations"):
        photo_media(media_representations=representations(original_mime_type=SVG))


def test_svg_display_is_rejected_for_photo() -> None:
    with pytest.raises(ValueError, match="SVG representations"):
        photo_media(media_representations=representations(display_mime_type=SVG))


def test_svg_thumbnail_is_rejected_for_photo() -> None:
    with pytest.raises(ValueError, match="SVG representations"):
        photo_media(
            media_representations=representations(
                thumbnails=((ThumbnailSize.SMALL, thumbnail_representation(SVG)),)
            )
        )


def test_svg_thumbnail_is_rejected_for_copy() -> None:
    with pytest.raises(ValueError, match="SVG representations"):
        copy_media(
            media_representations=representations(
                thumbnails=((ThumbnailSize.SMALL, thumbnail_representation(SVG)),)
            )
        )


def test_svg_copy_with_raster_previews_is_valid() -> None:
    result = copy_media(
        media_representations=MediaRepresentations(
            original_representation(SVG),
            ((ThumbnailSize.SMALL, thumbnail_representation("image/png")),),
            display=display_representation("image/png"),
        )
    )

    assert result.representations.original.mime_type == SVG


def test_raster_photo_with_every_representation_role_is_valid() -> None:
    result = photo_media(
        media_representations=representations(
            display_mime_type="image/jpeg",
            thumbnails=(
                (ThumbnailSize.SMALL, thumbnail_representation()),
                (ThumbnailSize.LARGE, thumbnail_representation()),
            ),
        )
    )

    assert all(
        representation.mime_type == "image/jpeg"
        for representation in result.representations.all_representations
    )


def test_all_representations_covers_original_display_and_thumbnails() -> None:
    original = original_representation()
    display = display_representation()
    small = thumbnail_representation()
    result = MediaRepresentations(
        original, ((ThumbnailSize.SMALL, small),), display=display
    )

    assert result.all_representations == (original, display, small)


def test_all_representations_omits_an_absent_display() -> None:
    original = original_representation()

    assert MediaRepresentations(original).all_representations == (original,)
