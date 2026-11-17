import uuid
from typing import Optional, cast, BinaryIO

from bson import ObjectId
from gridfs import GridFS, GridOut, NoFile
from pymongo.database import Database
from pymongo import ReadPreference

from ebl.media.application.media_errors import StoredRepresentationMissingError
from ebl.media.application.media_store import MediaRepresentationStore
from ebl.media.application.media_stored import (
    DisplayRepresentationWriteRequest,
    OpenRepresentation,
    OriginalRepresentationWriteRequest,
    ThumbnailRepresentationWriteRequest,
)
from ebl.media.application.media_storage_identity import (
    StoredRepresentationHandle,
    StoredRepresentationRole,
)
from ebl.media.domain import ThumbnailSize
from ebl.media.infrastructure.legacy_media_handles import (
    LEGACY_BUCKETS,
    LegacyRepresentationAdoption,
    legacy_handle,
)
from ebl.media.infrastructure.media_binary_validation import verified_content
from ebl.media.infrastructure.media_documents import handle_document
from ebl.media.infrastructure.media_indexes import (
    MEDIA_STORE_INDEXES,
    create_media_indexes,
)

OWNED_BUCKET = "media"
HANDLE_COLLECTION = "mediaFiles"


class GridFsMediaRepresentationStore(MediaRepresentationStore):
    def __init__(self, database: Database, *, max_file_size: int = 536870912) -> None:
        if (
            isinstance(max_file_size, bool)
            or not isinstance(max_file_size, int)
            or max_file_size <= 0
        ):
            raise ValueError("Media size limit must be a positive integer.")
        self._database = database.with_options(read_preference=ReadPreference.PRIMARY)
        self._registry = self._database[HANDLE_COLLECTION]
        self._max_file_size = max_file_size

    def create_indexes(self) -> None:
        create_media_indexes(self._database, MEDIA_STORE_INDEXES)

    def _record(self, handle: StoredRepresentationHandle) -> dict:
        record = self._registry.find_one(
            {"_id": handle.value, "handle": handle_document(handle)}
        )
        if record is None or record.get("deleted", False) or not record["ready"]:
            raise StoredRepresentationMissingError(handle)
        return record

    def _open(self, handle: StoredRepresentationHandle, record: dict) -> GridOut:
        bucket = record["bucket"]
        if (
            (record["ownership"] == "owned" and bucket != OWNED_BUCKET)
            or (record["ownership"] == "borrowed" and bucket not in LEGACY_BUCKETS)
            or record["ownership"] not in {"owned", "borrowed"}
        ):
            raise StoredRepresentationMissingError(handle)
        try:
            content = GridFS(self._database, bucket).get(record["fileId"])
        except NoFile as error:
            raise StoredRepresentationMissingError(handle) from error
        if (
            content.length != handle.representation.file_size
            or content.upload_date != record["uploadDate"]
        ):
            content.close()
            raise StoredRepresentationMissingError(handle)
        return content

    def open_representation(
        self, handle: StoredRepresentationHandle
    ) -> OpenRepresentation:
        content = self._open(handle, self._record(handle))
        return OpenRepresentation(
            handle.media_id,
            handle.representation,
            cast(BinaryIO, content),
            content.length,
        )

    def _write(
        self,
        request: OriginalRepresentationWriteRequest
        | DisplayRepresentationWriteRequest
        | ThumbnailRepresentationWriteRequest,
        role: StoredRepresentationRole,
        thumbnail_size: Optional[ThumbnailSize] = None,
    ) -> StoredRepresentationHandle:
        handle = StoredRepresentationHandle(
            request.media_id,
            str(uuid.uuid4()),
            request.representation,
            role=role,
            thumbnail_size=thumbnail_size,
        )
        with verified_content(
            request.content, request.representation, self._max_file_size
        ) as content:
            bucket = GridFS(self._database, OWNED_BUCKET)
            file_id = ObjectId()
            self._registry.insert_one(
                {
                    "_id": handle.value,
                    "handle": handle_document(handle),
                    "bucket": OWNED_BUCKET,
                    "fileId": file_id,
                    "uploadDate": None,
                    "ownership": "owned",
                    "deleted": False,
                    "ready": False,
                }
            )
            try:
                bucket.put(content, _id=file_id, metadata={"handle": handle.value})
                with bucket.get(file_id) as stored:
                    self._registry.update_one(
                        {"_id": handle.value},
                        {"$set": {"uploadDate": stored.upload_date, "ready": True}},
                    )
            except BaseException:
                self.delete_representation(handle)
                raise
        return handle

    def write_original(
        self, request: OriginalRepresentationWriteRequest
    ) -> StoredRepresentationHandle:
        return self._write(request, StoredRepresentationRole.ORIGINAL)

    def write_display(
        self, request: DisplayRepresentationWriteRequest
    ) -> StoredRepresentationHandle:
        return self._write(request, StoredRepresentationRole.DISPLAY)

    def write_thumbnail(
        self, request: ThumbnailRepresentationWriteRequest
    ) -> StoredRepresentationHandle:
        return self._write(
            request, StoredRepresentationRole.THUMBNAIL, request.thumbnail_size
        )

    def adopt_legacy(
        self, request: LegacyRepresentationAdoption
    ) -> StoredRepresentationHandle:
        handle = legacy_handle(request)
        try:
            with GridFS(self._database, request.container).get(
                request.file_id
            ) as original:
                with verified_content(
                    cast(BinaryIO, original),
                    request.representation,
                    self._max_file_size,
                    inspect_image=False,
                ):
                    upload_date = original.upload_date
        except NoFile as error:
            raise StoredRepresentationMissingError(handle) from error
        record = {
            "_id": handle.value,
            "handle": handle_document(handle),
            "bucket": request.container,
            "fileId": request.file_id,
            "uploadDate": upload_date,
            "ownership": "borrowed",
            "deleted": False,
            "ready": True,
        }
        self._registry.update_one(
            {"_id": handle.value}, {"$setOnInsert": record}, upsert=True
        )
        if self._registry.find_one(record) is None:
            raise ValueError(
                "A legacy representation handle cannot be reassigned or revived."
            )
        return handle

    def delete_representation(self, handle: StoredRepresentationHandle) -> None:
        record = self._registry.find_one(
            {"_id": handle.value, "handle": handle_document(handle)}
        )
        if record is None:
            return
        if record["ownership"] == "owned":
            if record["bucket"] != OWNED_BUCKET:
                raise StoredRepresentationMissingError(handle)
            GridFS(self._database, OWNED_BUCKET).delete(record["fileId"])
        elif (
            record["ownership"] != "borrowed" or record["bucket"] not in LEGACY_BUCKETS
        ):
            raise StoredRepresentationMissingError(handle)
        self._registry.update_one(record, {"$set": {"deleted": True}})
