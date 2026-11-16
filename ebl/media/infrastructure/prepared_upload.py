import logging
from dataclasses import dataclass
from typing import BinaryIO, Callable

from ebl.media.application.media_store import MediaRepresentationStore
from ebl.media.application.media_stored import (
    DisplayRepresentationWriteRequest,
    OriginalRepresentationWriteRequest,
    StoredMediaRepresentations,
    StoredThumbnailRepresentation,
    ThumbnailRepresentationWriteRequest,
)
from ebl.media.application.media_storage_identity import StoredRepresentationHandle
from ebl.media.domain import (
    MediaId,
    MediaRepresentation,
    MediaRepresentations,
    ThumbnailSize,
)

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class UploadContent:
    representation: MediaRepresentation
    content: BinaryIO


@dataclass(frozen=True)
class PreparedUpload:
    original: UploadContent
    display: UploadContent
    thumbnails: tuple[tuple[ThumbnailSize, UploadContent], ...]

    @property
    def representations(self) -> MediaRepresentations:
        return MediaRepresentations(
            self.original.representation,
            tuple((size, item.representation) for size, item in self.thumbnails),
            display=self.display.representation,
        )

    def store(
        self,
        store: MediaRepresentationStore,
        media_id: MediaId,
        on_staged: Callable[[StoredRepresentationHandle], None] | None = None,
    ) -> StoredMediaRepresentations:
        """Stage new versions, rolling back only these unpublished handles.

        The application must journal handles through ``on_staged`` and commit
        metadata only after this returns. A failed cleanup retains its registry
        record for reconciliation; it never exposes incomplete media metadata.
        Published-media removal must use the separate tombstone workflow.
        """
        handles: list[StoredRepresentationHandle] = []

        def record(handle: StoredRepresentationHandle) -> StoredRepresentationHandle:
            handles.append(handle)
            if on_staged is not None:
                on_staged(handle)
            return handle

        try:
            self.original.content.seek(0)
            original = record(
                store.write_original(
                    OriginalRepresentationWriteRequest(
                        media_id, self.original.content, self.original.representation
                    )
                )
            )
            self.display.content.seek(0)
            display = record(
                store.write_display(
                    DisplayRepresentationWriteRequest(
                        media_id, self.display.content, self.display.representation
                    )
                )
            )
            thumbnails = []
            for size, item in self.thumbnails:
                item.content.seek(0)
                handle = record(
                    store.write_thumbnail(
                        ThumbnailRepresentationWriteRequest(
                            media_id, item.content, item.representation, size
                        )
                    )
                )
                thumbnails.append(StoredThumbnailRepresentation(size, handle))
            return StoredMediaRepresentations(
                original, tuple(thumbnails), display=display
            )
        except BaseException:
            for handle in reversed(handles):
                try:
                    store.delete_representation(handle)
                except Exception:
                    LOGGER.exception(
                        "Upload staging cleanup failed for owned handle %s",
                        handle.value,
                    )
            raise
