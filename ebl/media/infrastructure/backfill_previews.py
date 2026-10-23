import io
from typing import BinaryIO, Callable

import attr

from ebl.media.application.media_store import MediaRepresentationStore
from ebl.media.application.media_stored import (
    DisplayRepresentationWriteRequest,
    StoredMedia,
    StoredMediaRepresentations,
    StoredThumbnailRepresentation,
    ThumbnailRepresentationWriteRequest,
)
from ebl.media.application.media_storage_identity import StoredRepresentationHandle
from ebl.media.domain import (
    Media,
    MediaChecksum,
    MediaRepresentation,
    MediaRepresentations,
    ThumbnailSize,
)
from ebl.media.infrastructure.backfill_images import checksum, preview_bytes
from PIL import Image


def preview_representation(content: bytes) -> MediaRepresentation:
    with Image.open(io.BytesIO(content)) as image:
        return MediaRepresentation(
            "image/jpeg",
            image.width,
            image.height,
            len(content),
            MediaChecksum(value=checksum(io.BytesIO(content))),
        )


class PreviewWriter:
    def __init__(
        self,
        store: MediaRepresentationStore,
        on_staged: Callable[[StoredRepresentationHandle], None] | None = None,
    ) -> None:
        self.store = store
        self.handles: list[StoredRepresentationHandle] = []
        self.on_staged = on_staged

    def _record(self, handle: StoredRepresentationHandle) -> None:
        self.handles.append(handle)
        if self.on_staged is not None:
            self.on_staged(handle)

    def create(
        self, media: Media, original: StoredRepresentationHandle, content: BinaryIO
    ) -> StoredMedia:
        display_bytes = preview_bytes(content, 2560)
        display_representation = preview_representation(display_bytes)
        display = self.store.write_display(
            DisplayRepresentationWriteRequest(
                media.id, io.BytesIO(display_bytes), display_representation
            )
        )
        self._record(display)
        thumbnail_representations = []
        thumbnails = []
        for size, pixels in (
            (ThumbnailSize.SMALL, 240),
            (ThumbnailSize.MEDIUM, 480),
            (ThumbnailSize.LARGE, 720),
        ):
            thumbnail_bytes = preview_bytes(content, pixels)
            representation = preview_representation(thumbnail_bytes)
            handle = self.store.write_thumbnail(
                ThumbnailRepresentationWriteRequest(
                    media.id, io.BytesIO(thumbnail_bytes), representation, size
                )
            )
            self._record(handle)
            thumbnail_representations.append((size, representation))
            thumbnails.append(StoredThumbnailRepresentation(size, handle))
        return StoredMedia(
            attr.evolve(
                media,
                representations=MediaRepresentations(
                    media.representations.original,
                    tuple(thumbnail_representations),
                    display=display_representation,
                ),
            ),
            StoredMediaRepresentations(original, tuple(thumbnails), display=display),
        )
