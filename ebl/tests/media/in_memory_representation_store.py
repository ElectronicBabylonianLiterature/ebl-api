import hashlib
from io import BytesIO
from typing import Dict, List, Optional

import attr

from ebl.media.application import (
    DisplayRepresentationWriteRequest,
    MediaRepresentationStore,
    OpenRepresentation,
    OriginalRepresentationWriteRequest,
    StoredRepresentationHandle,
    StoredRepresentationMissingError,
    StoredRepresentationRole,
    ThumbnailRepresentationWriteRequest,
)
from ebl.media.domain import MediaId, MediaRepresentation


@attr.s(auto_attribs=True, frozen=True)
class StoredRepresentationRecord:
    media_id: MediaId
    representation: MediaRepresentation
    content: bytes


class InMemoryRepresentationStore(MediaRepresentationStore):
    def __init__(self, call_log: Optional[List[str]] = None) -> None:
        self.written_originals: List[object] = []
        self.written_displays: List[object] = []
        self.written_thumbnails: List[object] = []
        self.deleted_handles: List[StoredRepresentationHandle] = []
        self.delete_failures: List[StoredRepresentationHandle] = []
        self.call_log = call_log if call_log is not None else []
        self._records: Dict[StoredRepresentationHandle, StoredRepresentationRecord] = {}
        self._next_handle = 0

    def open_representation(
        self, handle: StoredRepresentationHandle
    ) -> OpenRepresentation:
        try:
            record = self._records[handle]
        except KeyError as error:
            raise StoredRepresentationMissingError(handle) from error
        return OpenRepresentation(
            media_id=record.media_id,
            representation=record.representation,
            content=BytesIO(record.content),
            length=len(record.content),
        )

    def write_original(
        self, request: OriginalRepresentationWriteRequest
    ) -> StoredRepresentationHandle:
        self.written_originals.append(request)
        return self._write(request)

    def write_display(
        self, request: DisplayRepresentationWriteRequest
    ) -> StoredRepresentationHandle:
        self.written_displays.append(request)
        return self._write(request)

    def write_thumbnail(
        self, request: ThumbnailRepresentationWriteRequest
    ) -> StoredRepresentationHandle:
        self.written_thumbnails.append(request)
        return self._write(request)

    def delete_representation(self, handle: StoredRepresentationHandle) -> None:
        self.call_log.append("store.delete_representation")
        if handle in self.delete_failures:
            raise RuntimeError("Stored representation delete failed.")
        self.deleted_handles.append(handle)
        self._records.pop(handle, None)

    def fail_deleting(self, handle: StoredRepresentationHandle) -> None:
        self.delete_failures.append(handle)

    def contains(self, handle: StoredRepresentationHandle) -> bool:
        return handle in self._records

    def _write(
        self,
        request: OriginalRepresentationWriteRequest
        | DisplayRepresentationWriteRequest
        | ThumbnailRepresentationWriteRequest,
    ) -> StoredRepresentationHandle:
        content = request.content.read()
        if len(content) != request.representation.file_size:
            raise ValueError("Stored byte count must match representation metadata.")
        checksum = request.representation.checksum
        if (
            checksum is not None
            and hashlib.sha256(content).hexdigest() != checksum.value
        ):
            raise ValueError("Stored checksum must match representation metadata.")
        self._next_handle += 1
        role = StoredRepresentationRole.ORIGINAL
        thumbnail_size = None
        if isinstance(request, DisplayRepresentationWriteRequest):
            role = StoredRepresentationRole.DISPLAY
        elif isinstance(request, ThumbnailRepresentationWriteRequest):
            role = StoredRepresentationRole.THUMBNAIL
            thumbnail_size = request.thumbnail_size
        handle = StoredRepresentationHandle(
            request.media_id,
            f"stored-representation-{self._next_handle}",
            request.representation,
            role=role,
            thumbnail_size=thumbnail_size,
        )
        self._records[handle] = StoredRepresentationRecord(
            request.media_id, request.representation, content
        )
        return handle
