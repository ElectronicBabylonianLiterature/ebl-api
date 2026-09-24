from abc import ABC, abstractmethod

from ebl.media.application.media_stored import (
    DisplayRepresentationWriteRequest,
    OpenRepresentation,
    OriginalRepresentationWriteRequest,
    ThumbnailRepresentationWriteRequest,
)
from ebl.media.application.media_storage_identity import StoredRepresentationHandle


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

        The returned media id and byte length must match the requested handle's
        owner and representation metadata.
        """
        raise NotImplementedError

    @abstractmethod
    def write_original(
        self, request: OriginalRepresentationWriteRequest
    ) -> StoredRepresentationHandle:
        """Store an original and return a NEW logical version handle.

        Every successful write creates a new independently addressable logical
        stored version. Its opaque handle value must never have been returned by
        any previous write, even after deletion. Existing handles keep
        identifying their existing bytes until that exact handle is deleted. A
        provider may deduplicate physical bytes only if deleting one logical
        handle cannot break another. Returning or reissuing a stable handle
        whose bytes were overwritten is a defect: stale cleanup could delete a
        newer generation.

        Implementations must enforce upload limits while streaming, determine
        the actual MIME type, and verify the byte count and SHA-256 checksum
        against the supplied representation metadata before committing. SVG
        originals must be sanitized before they become readable.
        """
        raise NotImplementedError

    @abstractmethod
    def write_display(
        self, request: DisplayRepresentationWriteRequest
    ) -> StoredRepresentationHandle:
        """Store a display with all integrity checks defined by `write_original`."""
        raise NotImplementedError

    @abstractmethod
    def write_thumbnail(
        self, request: ThumbnailRepresentationWriteRequest
    ) -> StoredRepresentationHandle:
        """Store a thumbnail with all integrity checks defined by `write_original`."""
        raise NotImplementedError

    @abstractmethod
    def delete_representation(self, handle: StoredRepresentationHandle) -> None:
        """Delete exactly the one logical version named; idempotent when absent.

        Must not affect any other handle, including handles that share bytes.
        """
        raise NotImplementedError
