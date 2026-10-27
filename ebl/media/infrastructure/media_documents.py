import json
from typing import Optional

from ebl.common.domain.project import ResearchProject
from ebl.media.application.media_stored import (
    StoredMedia,
    StoredMediaRepresentations,
    StoredThumbnailRepresentation,
)
from ebl.media.application.media_storage_identity import (
    StoredRepresentationHandle,
    StoredRepresentationRole,
)
from ebl.media.domain import (
    Media,
    MediaAssociation,
    MediaChecksum,
    MediaId,
    MediaImportSource,
    MediaReference,
    MediaRepresentation,
    MediaRepresentations,
    MediaType,
    ThumbnailSize,
)


def source_document(source: MediaImportSource) -> dict:
    return {
        "system": source.system,
        "container": source.container,
        "fileId": source.file_id,
    }


def source_key(source: MediaImportSource) -> str:
    return json.dumps(source_document(source), sort_keys=True, separators=(",", ":"))


def representation_document(representation: MediaRepresentation) -> dict:
    return {
        "mimeType": representation.mime_type,
        "width": representation.width,
        "height": representation.height,
        "fileSize": representation.file_size,
        "checksum": (
            representation.checksum.value if representation.checksum else None
        ),
    }


def load_representation(document: dict) -> MediaRepresentation:
    return MediaRepresentation(
        document["mimeType"],
        document["width"],
        document["height"],
        document["fileSize"],
        MediaChecksum(value=document["checksum"]) if document["checksum"] else None,
    )


def handle_document(handle: StoredRepresentationHandle) -> dict:
    return {
        "mediaId": str(handle.media_id),
        "value": handle.value,
        "representation": representation_document(handle.representation),
        "role": handle.role.value,
        "thumbnailSize": handle.thumbnail_size.value if handle.thumbnail_size else None,
    }


def load_handle(document: dict) -> StoredRepresentationHandle:
    return StoredRepresentationHandle(
        MediaId(document["mediaId"]),
        document["value"],
        load_representation(document["representation"]),
        role=StoredRepresentationRole(document["role"]),
        thumbnail_size=(
            ThumbnailSize(document["thumbnailSize"])
            if document["thumbnailSize"]
            else None
        ),
    )


def stored_document(stored: StoredMedia) -> dict:
    media = stored.media
    handles = stored.representations
    document = {
        "_id": str(media.id),
        "state": "active",
        "type": media.type.value,
        "originalFilename": media.original_filename,
        "associations": [
            {
                "fragmentId": str(association.fragment_id),
                "sortOrder": association.sort_order,
                "isPrimary": association.is_primary,
            }
            for association in media.associations
        ],
        "projects": [project.name for project in media.projects],
        "references": [reference.bibliography_id for reference in media.references],
        "caption": media.caption,
        "attribution": media.attribution,
        "representations": {
            "original": handle_document(handles.original),
            "display": handle_document(handles.display) if handles.display else None,
            "thumbnails": {
                thumbnail.size.value: handle_document(thumbnail.handle)
                for thumbnail in handles.thumbnails
            },
        },
    }
    import_source = media.import_source
    if import_source is not None:
        document["importSource"] = source_document(import_source)
        document["sourceKey"] = source_key(import_source)
    return document


def _load_source(document: dict) -> Optional[MediaImportSource]:
    source = document.get("importSource")
    return (
        MediaImportSource(
            source["system"], source["fileId"], container=source["container"]
        )
        if source
        else None
    )


def load_stored(document: dict) -> StoredMedia:
    representations = document["representations"]
    original = load_handle(representations["original"])
    display = (
        load_handle(representations["display"]) if representations["display"] else None
    )
    thumbnails = tuple(
        StoredThumbnailRepresentation(ThumbnailSize(size), load_handle(handle))
        for size, handle in representations["thumbnails"].items()
    )
    media = Media(
        id=document["_id"],
        type=MediaType(document["type"]),
        original_filename=document["originalFilename"],
        representations=MediaRepresentations(
            original.representation,
            tuple(
                (thumbnail.size, thumbnail.handle.representation)
                for thumbnail in thumbnails
            ),
            display=display.representation if display else None,
        ),
        associations=tuple(
            MediaAssociation(
                association["fragmentId"],
                association["sortOrder"],
                association["isPrimary"],
            )
            for association in document["associations"]
        ),
        projects=tuple(ResearchProject[project] for project in document["projects"]),
        references=tuple(
            MediaReference(reference) for reference in document["references"]
        ),
        caption=document["caption"],
        attribution=document["attribution"],
        import_source=_load_source(document),
    )
    return StoredMedia(
        media,
        StoredMediaRepresentations(original, thumbnails, display=display),
        deletion_token=document.get("deletionToken"),
    )
