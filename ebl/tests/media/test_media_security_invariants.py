import pytest

from ebl.media.domain import MediaRepresentations, ThumbnailSize
from ebl.tests.media.factories import (
    copy_media,
    display_representation,
    medium_thumbnail_representation,
    original_representation,
    photo_media,
    representations,
    thumbnail_representation,
)

SVG = "image/svg+xml"
SUPPORTED_RASTER_MIME_TYPES = ("image/jpeg", "image/png", "image/webp")
UNSUPPORTED_ORIGINAL_MIME_TYPES = (SVG, "text/html", "application/pdf", "audio/mpeg")
UNSUPPORTED_PREVIEW_MIME_TYPES = (
    SVG,
    "IMAGE/SVG+XML",
    "image/svg+xml; charset=utf-8",
    "text/html",
    "application/pdf",
    "audio/mpeg",
)


@pytest.mark.parametrize("mime_type", SUPPORTED_RASTER_MIME_TYPES)
def test_supported_raster_originals_are_valid_for_photo(mime_type) -> None:
    result = photo_media(
        media_representations=representations(original_mime_type=mime_type)
    )

    assert result.representations.original.mime_type == mime_type


@pytest.mark.parametrize("mime_type", SUPPORTED_RASTER_MIME_TYPES)
def test_supported_raster_originals_are_valid_for_copy(mime_type) -> None:
    result = copy_media(
        media_representations=representations(original_mime_type=mime_type)
    )

    assert result.representations.original.mime_type == mime_type


def test_svg_original_is_valid_for_copy() -> None:
    result = copy_media(
        media_representations=representations(
            original_mime_type=SVG, display_mime_type="image/jpeg"
        )
    )

    assert result.representations.original.mime_type == SVG


@pytest.mark.parametrize("mime_type", UNSUPPORTED_ORIGINAL_MIME_TYPES)
def test_unsupported_original_mime_is_rejected_for_photo(mime_type) -> None:
    with pytest.raises(ValueError, match="MIME types"):
        photo_media(media_representations=representations(original_mime_type=mime_type))


@pytest.mark.parametrize("mime_type", ("text/html", "application/pdf", "audio/mpeg"))
def test_unsupported_original_mime_is_rejected_for_copy(mime_type) -> None:
    with pytest.raises(ValueError, match="MIME types"):
        copy_media(media_representations=representations(original_mime_type=mime_type))


@pytest.mark.parametrize("media_factory", (photo_media, copy_media))
@pytest.mark.parametrize("mime_type", UNSUPPORTED_PREVIEW_MIME_TYPES)
def test_unsupported_display_mime_is_rejected_for_preview_roles(
    media_factory, mime_type
) -> None:
    with pytest.raises(ValueError, match="MIME types"):
        media_factory(
            media_representations=representations(display_mime_type=mime_type)
        )


@pytest.mark.parametrize("media_factory", (photo_media, copy_media))
@pytest.mark.parametrize("mime_type", UNSUPPORTED_PREVIEW_MIME_TYPES)
def test_unsupported_thumbnail_mime_is_rejected_for_preview_roles(
    media_factory, mime_type
) -> None:
    with pytest.raises(ValueError, match="MIME types"):
        media_factory(
            media_representations=representations(
                thumbnails=((ThumbnailSize.SMALL, thumbnail_representation(mime_type)),)
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


def test_svg_copy_with_raster_thumbnail_without_display_is_valid() -> None:
    result = copy_media(
        media_representations=MediaRepresentations(
            original_representation(SVG),
            ((ThumbnailSize.MEDIUM, medium_thumbnail_representation("image/webp")),),
        )
    )

    assert result.representations.original.mime_type == SVG
    assert result.representations.thumbnails[0][0] is ThumbnailSize.MEDIUM


def test_mime_types_are_normalized_before_validation() -> None:
    result = copy_media(
        media_representations=representations(
            original_mime_type=" IMAGE/SVG+XML; charset=utf-8 ",
            display_mime_type=" IMAGE/JPEG ",
            thumbnails=(
                (ThumbnailSize.SMALL, thumbnail_representation(" image/png ")),
            ),
        )
    )

    assert result.representations.original.mime_type == SVG
    assert result.representations.display is not None
    assert result.representations.display.mime_type == "image/jpeg"
    assert result.representations.thumbnails[0][1].mime_type == "image/png"


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
