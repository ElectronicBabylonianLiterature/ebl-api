from collections.abc import Callable
from io import BytesIO
from typing import cast

import pytest

from ebl.media.application import (
    DisplayRepresentationWriteRequest,
    OpenRepresentation,
    OriginalRepresentationWriteRequest,
    ThumbnailRepresentationWriteRequest,
)
from ebl.media.domain import MediaId, MediaRepresentation, ThumbnailSize
from ebl.tests.media.factories import media_id, original_representation

PHOTO_ID = MediaId("550e8400-e29b-41d4-a716-446655440000")


def write_content() -> BytesIO:
    return BytesIO(b"media-bytes")


def test_open_representation_validates_core_fields() -> None:
    with pytest.raises(ValueError, match="media_id must be a MediaId"):
        OpenRepresentation(
            media_id=cast(MediaId, "not-a-media-id"),
            representation=original_representation(),
            content=write_content(),
            length=len(b"media-bytes"),
        )
    with pytest.raises(
        ValueError, match="representation must be a MediaRepresentation"
    ):
        OpenRepresentation(
            media_id=PHOTO_ID,
            representation=cast(MediaRepresentation, "not-a-representation"),
            content=write_content(),
            length=len(b"media-bytes"),
        )
    with pytest.raises(ValueError, match="content must be a readable stream"):
        OpenRepresentation(
            media_id=PHOTO_ID,
            representation=original_representation(),
            content=cast(BytesIO, object()),
            length=len(b"media-bytes"),
        )


def test_representation_write_requests_validate_core_fields() -> None:
    with pytest.raises(ValueError, match="media_id must be a MediaId"):
        OriginalRepresentationWriteRequest(
            cast(MediaId, "not-a-media-id"),
            write_content(),
            original_representation(),
        )
    with pytest.raises(ValueError, match="content must be a readable stream"):
        OriginalRepresentationWriteRequest(
            media_id(), cast(BytesIO, object()), original_representation()
        )
    with pytest.raises(
        ValueError, match="representation must be a MediaRepresentation"
    ):
        OriginalRepresentationWriteRequest(
            media_id(),
            write_content(),
            cast(MediaRepresentation, "not-a-representation"),
        )


def test_original_write_request_requires_a_checksum() -> None:
    representation = MediaRepresentation("image/jpeg", 1, 1, 1)

    with pytest.raises(ValueError, match="must contain a checksum"):
        OriginalRepresentationWriteRequest(media_id(), write_content(), representation)


def test_thumbnail_write_request_rejects_invalid_thumbnail_size() -> None:
    with pytest.raises(ValueError, match="thumbnail_size must be a ThumbnailSize"):
        ThumbnailRepresentationWriteRequest(
            media_id(),
            write_content(),
            original_representation(),
            cast(ThumbnailSize, None),
        )


@pytest.mark.parametrize(
    "request_type",
    (DisplayRepresentationWriteRequest, ThumbnailRepresentationWriteRequest),
)
def test_preview_write_requests_reject_svg(
    request_type: Callable[..., object],
) -> None:
    kwargs = (
        {"thumbnail_size": ThumbnailSize.SMALL}
        if request_type is ThumbnailRepresentationWriteRequest
        else {}
    )

    with pytest.raises(ValueError, match="must be raster"):
        request_type(
            media_id(),
            write_content(),
            original_representation("image/svg+xml"),
            **kwargs,
        )
