from io import BytesIO
from typing import Any, cast

import pytest

from ebl.media.application import (
    DisplayRepresentationWriteRequest,
    MediaRepresentationStore,
    OriginalRepresentationWriteRequest,
    ThumbnailRepresentationWriteRequest,
)
from ebl.media.domain import ThumbnailSize
from ebl.tests.media.factories import media_id, original_representation


class RecordingRepresentationStore(MediaRepresentationStore):
    def __init__(self):
        self.original_request = None
        self.display_request = None
        self.thumbnail_request = None

    def read_original(self, media):
        raise NotImplementedError

    def read_display(self, media):
        raise NotImplementedError

    def read_thumbnail(self, media, thumbnail_size):
        raise NotImplementedError

    def write_original(self, request: OriginalRepresentationWriteRequest):
        self.original_request = request

    def write_display(self, request: DisplayRepresentationWriteRequest):
        self.display_request = request

    def write_thumbnail(self, request: ThumbnailRepresentationWriteRequest):
        self.thumbnail_request = request

    def delete_representations(self, media_id_):
        raise NotImplementedError


def write_content():
    return BytesIO(b"media-bytes")


def make_request(request_type: Any, **kwargs: Any) -> Any:
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
        ThumbnailRepresentationWriteRequest(
            media_id(), write_content(), original_representation()
        )


def test_thumbnail_write_request_rejects_invalid_thumbnail_size() -> None:
    with pytest.raises(TypeError):
        ThumbnailRepresentationWriteRequest(
            media_id(),
            write_content(),
            original_representation(),
            cast(ThumbnailSize, None),
        )


def test_representation_store_writes_accept_operation_specific_requests() -> None:
    original_request = OriginalRepresentationWriteRequest(
        media_id(), write_content(), original_representation()
    )
    display_request = DisplayRepresentationWriteRequest(
        media_id(), write_content(), original_representation()
    )
    thumbnail_request = ThumbnailRepresentationWriteRequest(
        media_id(), write_content(), original_representation(), ThumbnailSize.SMALL
    )
    store = RecordingRepresentationStore()

    store.write_original(original_request)
    store.write_display(display_request)
    store.write_thumbnail(thumbnail_request)

    assert store.original_request == original_request
    assert store.display_request == display_request
    assert store.thumbnail_request == thumbnail_request
