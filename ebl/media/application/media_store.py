from abc import ABC, abstractmethod

from ebl.media.application.media_stored import (
    DisplayRepresentationWriteRequest,
    OpenRepresentation,
    OriginalRepresentationWriteRequest,
    StoredRepresentationHandle,
    ThumbnailRepresentationWriteRequest,
)
from ebl.media.domain import MediaId


class MediaRepresentationStore(ABC):
    @abstractmethod
    def open_representation(
        self, handle: StoredRepresentationHandle
    ) -> OpenRepresentation:
        """Open the exact logical stored version the handle identifies.

        Raises `StoredRepresentationMissingError` when the handle is unknown:
        metadata referencing absent bytes is a storage-integrity failure, not a
        client error. The caller owns the returned stream and must close it.
        Implementations may stream rather than buffer, and callers must not
        assume the stream is seekable.
        """
        raise NotImplementedError

    @abstractmethod
    def write_original(
        self, request: OriginalRepresentationWriteRequest
    ) -> StoredRepresentationHandle:
        """Store an original and return a NEW logical version handle.

        Every successful write creates a new independently addressable logical
        stored version, and returns a handle different from every still-live
        handle it replaces. Existing handles keep identifying their existing
        bytes until that exact handle is deleted. A provider may deduplicate
        physical bytes only if deleting one logical handle cannot break another.
        Returning a stable handle whose bytes were overwritten is a defect: it
        makes replacement destroy the current version.
        """
        raise NotImplementedError

    @abstractmethod
    def write_display(
        self, request: DisplayRepresentationWriteRequest
    ) -> StoredRepresentationHandle:
        """Store a display representation. New logical version per `write_original`."""
        raise NotImplementedError

    @abstractmethod
    def write_thumbnail(
        self, request: ThumbnailRepresentationWriteRequest
    ) -> StoredRepresentationHandle:
        """Store one thumbnail. New logical version per `write_original`."""
        raise NotImplementedError

    @abstractmethod
    def delete_representation(self, handle: StoredRepresentationHandle) -> None:
        """Delete exactly the one logical version named; idempotent when absent.

        Must not affect any other handle, including handles that share bytes.
        """
        raise NotImplementedError

    @abstractmethod
    def delete_representations(self, media_id: MediaId) -> None:
        """Delete every logical version owned by this media; idempotent.

        Must never touch versions owned by another media id.
        """
        raise NotImplementedError
