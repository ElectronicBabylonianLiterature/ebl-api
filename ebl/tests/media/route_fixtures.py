from io import BytesIO
from typing import Mapping, Optional

from ebl.media.application import (
    DisplayRepresentationWriteRequest,
    OriginalRepresentationWriteRequest,
    StoredMedia,
    StoredMediaRepresentations,
    StoredRepresentationHandle,
    StoredThumbnailRepresentation,
    ThumbnailRepresentationWriteRequest,
)
from ebl.media.domain import Media, ThumbnailSize
from ebl.media.infrastructure.grid_fs_media_store import (
    GridFsMediaRepresentationStore,
)
from ebl.media.infrastructure.mongo_media_repository import MongoMediaRepository

ORIGINAL_BYTES = b"original-image-bytes"
DISPLAY_BYTES = b"display-image-bytes"
THUMBNAIL_BYTES: Mapping[ThumbnailSize, bytes] = {
    ThumbnailSize.SMALL: b"small-thumbnail-bytes",
    ThumbnailSize.MEDIUM: b"medium-thumbnail-bytes",
    ThumbnailSize.LARGE: b"large-thumbnail-bytes",
}


def _display_handle(
    store: GridFsMediaRepresentationStore, media: Media
) -> Optional[StoredRepresentationHandle]:
    display = media.representations.display
    return (
        None
        if display is None
        else store.write_display(
            DisplayRepresentationWriteRequest(media.id, BytesIO(DISPLAY_BYTES), display)
        )
    )


def seed_media(
    repository: MongoMediaRepository,
    store: GridFsMediaRepresentationStore,
    media: Media,
) -> StoredMedia:
    stored = StoredMedia(
        media,
        StoredMediaRepresentations(
            store.write_original(
                OriginalRepresentationWriteRequest(
                    media.id, BytesIO(ORIGINAL_BYTES), media.representations.original
                )
            ),
            tuple(
                StoredThumbnailRepresentation(
                    size,
                    store.write_thumbnail(
                        ThumbnailRepresentationWriteRequest(
                            media.id,
                            BytesIO(THUMBNAIL_BYTES[size]),
                            representation,
                            size,
                        )
                    ),
                )
                for size, representation in media.representations.thumbnails
            ),
            display=_display_handle(store, media),
        ),
    )
    repository.create(stored)
    return stored
