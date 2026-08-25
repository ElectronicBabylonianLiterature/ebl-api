import io
from typing import TYPE_CHECKING, Any, Mapping, Optional, Union

from bson import ObjectId
from bson.errors import InvalidId
from gridfs import GridFS, GridOut, NoFile
from pymongo.database import Database

from ebl.errors import Defect
from ebl.media.application.media_errors import StoredRepresentationMissingError
from ebl.media.application.media_store import MediaRepresentationStore
from ebl.media.application.media_stored import (
    DisplayRepresentationWriteRequest,
    OpenRepresentation,
    OriginalRepresentationWriteRequest,
    StoredRepresentationHandle,
    ThumbnailRepresentationWriteRequest,
)
from ebl.media.domain import MediaChecksum, MediaId, MediaRepresentation

if TYPE_CHECKING:
    from _typeshed import WriteableBuffer

BUCKET = "mediaRepresentations"
MEDIA_ID = "metadata.mediaId"

RepresentationWriteRequest = Union[
    OriginalRepresentationWriteRequest,
    DisplayRepresentationWriteRequest,
    ThumbnailRepresentationWriteRequest,
]

ORIGINAL_ROLE = "original"
DISPLAY_ROLE = "display"
THUMBNAIL_ROLE = "thumbnail"


class GridOutStream(io.RawIOBase):
    def __init__(self, grid_out: GridOut) -> None:
        self._grid_out = grid_out

    def readable(self) -> bool:
        return True

    def readinto(self, buffer: "WriteableBuffer") -> int:
        target = memoryview(buffer)
        data = self._grid_out.read(len(target))
        target[: len(data)] = data
        return len(data)

    def close(self) -> None:
        self._grid_out.close()
        super().close()


def _representation_metadata(representation: MediaRepresentation) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "mimeType": representation.mime_type,
        "width": representation.width,
        "height": representation.height,
        "fileSize": representation.file_size,
    }
    if representation.checksum is not None:
        metadata["checksum"] = {
            "algorithm": representation.checksum.algorithm,
            "value": representation.checksum.value,
        }
    return metadata


def _checksum_of(metadata: Mapping[str, Any]) -> Optional[MediaChecksum]:
    checksum = metadata.get("checksum")
    return (
        None
        if checksum is None
        else MediaChecksum(checksum["algorithm"], checksum["value"])
    )


def _object_id_of(handle: StoredRepresentationHandle) -> Optional[ObjectId]:
    try:
        return ObjectId(handle.value)
    except (InvalidId, TypeError):
        return None


class GridFsMediaRepresentationStore(MediaRepresentationStore):
    def __init__(self, database: Database, bucket: str = BUCKET) -> None:
        self._fs = GridFS(database, bucket)
        self._files = database[f"{bucket}.files"]

    def create_indexes(self) -> None:
        self._files.create_index(MEDIA_ID)

    def open_representation(
        self, handle: StoredRepresentationHandle
    ) -> OpenRepresentation:
        grid_out = self._get(handle)
        metadata = grid_out.metadata
        if not isinstance(metadata, Mapping):
            grid_out.close()
            raise Defect("Stored media representation metadata is missing.")
        return self._open_representation(grid_out, metadata)

    def write_original(
        self, request: OriginalRepresentationWriteRequest
    ) -> StoredRepresentationHandle:
        return self._write(request, ORIGINAL_ROLE)

    def write_display(
        self, request: DisplayRepresentationWriteRequest
    ) -> StoredRepresentationHandle:
        return self._write(request, DISPLAY_ROLE)

    def write_thumbnail(
        self, request: ThumbnailRepresentationWriteRequest
    ) -> StoredRepresentationHandle:
        return self._write(
            request, THUMBNAIL_ROLE, {"thumbnailSize": request.thumbnail_size.value}
        )

    def delete_representation(self, handle: StoredRepresentationHandle) -> None:
        object_id = _object_id_of(handle)
        if object_id is not None:
            self._fs.delete(object_id)

    def delete_representations(self, media_id: MediaId) -> None:
        for document in self._files.find({MEDIA_ID: str(media_id)}, {"_id": 1}):
            self._fs.delete(document["_id"])

    def _get(self, handle: StoredRepresentationHandle) -> GridOut:
        object_id = _object_id_of(handle)
        if object_id is None:
            raise StoredRepresentationMissingError(handle)
        try:
            return self._fs.get(object_id)
        except NoFile as error:
            raise StoredRepresentationMissingError(handle) from error

    def _open_representation(
        self, grid_out: GridOut, metadata: Mapping[str, Any]
    ) -> OpenRepresentation:
        try:
            representation = MediaRepresentation(
                metadata["mimeType"],
                metadata["width"],
                metadata["height"],
                metadata["fileSize"],
                _checksum_of(metadata),
            )
            media_id = MediaId(metadata["mediaId"])
            length = grid_out.length
            if length <= 0:
                raise ValueError("Stored representation is empty.")
        except (KeyError, TypeError, ValueError) as error:
            grid_out.close()
            raise Defect("Stored media representation metadata is invalid.") from error
        return OpenRepresentation(
            media_id=media_id,
            representation=representation,
            content=io.BufferedReader(GridOutStream(grid_out)),
            length=length,
        )

    def _write(
        self,
        request: RepresentationWriteRequest,
        role: str,
        extra_metadata: Optional[Mapping[str, Any]] = None,
    ) -> StoredRepresentationHandle:
        metadata = {
            "mediaId": str(request.media_id),
            "role": role,
            **_representation_metadata(request.representation),
            **(extra_metadata or {}),
        }
        object_id = self._fs.put(
            request.content,
            metadata=metadata,
            contentType=request.representation.mime_type,
        )
        return StoredRepresentationHandle(str(object_id))
