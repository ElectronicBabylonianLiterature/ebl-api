import json
import uuid
from typing import Optional

from bson import ObjectId
import attr

from ebl.media.application.media_storage_identity import (
    StoredRepresentationHandle,
    StoredRepresentationRole,
)
from ebl.media.domain import (
    MediaId,
    MediaImportSource,
    MediaRepresentation,
    ThumbnailSize,
)
from ebl.media.infrastructure.media_documents import (
    representation_document,
    source_document,
)

LEGACY_BUCKETS = frozenset({"photos", "thumbnails"})


@attr.s(auto_attribs=True, frozen=True)
class LegacyRepresentationAdoption:
    media_id: MediaId
    container: str
    file_id: ObjectId | str
    representation: MediaRepresentation
    role: StoredRepresentationRole = attr.ib(
        default=StoredRepresentationRole.ORIGINAL, kw_only=True
    )
    thumbnail_size: Optional[ThumbnailSize] = attr.ib(default=None, kw_only=True)


def legacy_import_source(container: str, file_id: ObjectId | str) -> MediaImportSource:
    if container not in LEGACY_BUCKETS:
        raise ValueError("Only legacy photo and thumbnail buckets can be adopted.")
    if not isinstance(file_id, (ObjectId, str)) or not str(file_id):
        raise ValueError("Legacy file identity must be a nonempty string or ObjectId.")
    typed_identity = (
        f"{'ObjectId' if isinstance(file_id, ObjectId) else 'str'}:{file_id}"
    )
    return MediaImportSource("gridfs", typed_identity, container=container)


def legacy_handle(request: LegacyRepresentationAdoption) -> StoredRepresentationHandle:
    identity = {
        "source": source_document(
            legacy_import_source(request.container, request.file_id)
        ),
        "mediaId": str(request.media_id),
        "representation": representation_document(request.representation),
        "role": request.role.value,
        "thumbnailSize": request.thumbnail_size.value
        if request.thumbnail_size
        else None,
    }
    value = str(uuid.uuid5(uuid.NAMESPACE_URL, json.dumps(identity, sort_keys=True)))
    return StoredRepresentationHandle(
        request.media_id,
        value,
        request.representation,
        role=request.role,
        thumbnail_size=request.thumbnail_size,
    )
