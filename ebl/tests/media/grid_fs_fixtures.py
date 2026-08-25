from io import BytesIO
from typing import Optional

import pytest
from bson import ObjectId
from pymongo.database import Database

from ebl.media.application import (
    DisplayRepresentationWriteRequest,
    OriginalRepresentationWriteRequest,
    StoredRepresentationHandle,
    ThumbnailRepresentationWriteRequest,
)
from ebl.media.domain import MediaId, MediaRepresentation, ThumbnailSize
from ebl.media.infrastructure.grid_fs_media_store import (
    GridFsMediaRepresentationStore,
)
from ebl.tests.media.factories import (
    display_representation,
    original_representation,
    thumbnail_representation,
)

MEDIA_ID = MediaId("550e8400-e29b-41d4-a716-446655440000")
OTHER_MEDIA_ID = MediaId("550e8400-e29b-41d4-a716-446655440001")
ORIGINAL_BYTES = b"original-bytes"
DISPLAY_BYTES = b"display-bytes"
THUMBNAIL_BYTES = b"thumbnail-bytes"
UNKNOWN_HANDLE = StoredRepresentationHandle("000000000000000000000000")
UNPARSABLE_HANDLE = StoredRepresentationHandle("not-an-object-id")


@pytest.fixture
def store(database: Database) -> GridFsMediaRepresentationStore:
    return GridFsMediaRepresentationStore(database)


def write_original(
    store: GridFsMediaRepresentationStore,
    media_id: MediaId = MEDIA_ID,
    content: bytes = ORIGINAL_BYTES,
    representation: Optional[MediaRepresentation] = None,
) -> StoredRepresentationHandle:
    return store.write_original(
        OriginalRepresentationWriteRequest(
            media_id, BytesIO(content), representation or original_representation()
        )
    )


def write_display(
    store: GridFsMediaRepresentationStore, media_id: MediaId = MEDIA_ID
) -> StoredRepresentationHandle:
    return store.write_display(
        DisplayRepresentationWriteRequest(
            media_id, BytesIO(DISPLAY_BYTES), display_representation()
        )
    )


def write_thumbnail(
    store: GridFsMediaRepresentationStore,
    media_id: MediaId = MEDIA_ID,
    size: ThumbnailSize = ThumbnailSize.SMALL,
) -> StoredRepresentationHandle:
    return store.write_thumbnail(
        ThumbnailRepresentationWriteRequest(
            media_id, BytesIO(THUMBNAIL_BYTES), thumbnail_representation(), size
        )
    )


def read_representation(
    store: GridFsMediaRepresentationStore, handle: StoredRepresentationHandle
) -> bytes:
    opened = store.open_representation(handle)
    try:
        return opened.content.read()
    finally:
        opened.content.close()


def object_id_of(handle: StoredRepresentationHandle) -> ObjectId:
    return ObjectId(handle.value)
