from typing import Any, Mapping, Optional, Sequence

from ebl.common.domain.project import ResearchProject
from ebl.media.application.media_stored import (
    StoredMedia,
    StoredMediaRepresentations,
    StoredRepresentationHandle,
    StoredThumbnailRepresentation,
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
from ebl.transliteration.domain.museum_number import MuseumNumber

STORED_HANDLE = "storedHandle"

PROJECTS_BY_ABBREVIATION = {
    project.abbreviation: project for project in ResearchProject
}


def _checksum_document(checksum: MediaChecksum) -> dict[str, Any]:
    return {"algorithm": checksum.algorithm, "value": checksum.value}


def _checksum_of(document: Optional[Mapping[str, Any]]) -> Optional[MediaChecksum]:
    return (
        None
        if document is None
        else MediaChecksum(document["algorithm"], document["value"])
    )


def _representation_document(
    representation: MediaRepresentation, handle: StoredRepresentationHandle
) -> dict[str, Any]:
    document: dict[str, Any] = {
        STORED_HANDLE: handle.value,
        "mimeType": representation.mime_type,
        "width": representation.width,
        "height": representation.height,
        "fileSize": representation.file_size,
    }
    if representation.checksum is not None:
        document["checksum"] = _checksum_document(representation.checksum)
    return document


def _representation_of(document: Mapping[str, Any]) -> MediaRepresentation:
    return MediaRepresentation(
        document["mimeType"],
        document["width"],
        document["height"],
        document["fileSize"],
        _checksum_of(document.get("checksum")),
    )


def _handle_of(document: Mapping[str, Any]) -> StoredRepresentationHandle:
    return StoredRepresentationHandle(document[STORED_HANDLE])


def _association_document(association: MediaAssociation) -> dict[str, Any]:
    return {
        "fragmentId": str(association.fragment_id),
        "sortOrder": association.sort_order,
        "isPrimary": association.is_primary,
    }


def _association_of(document: Mapping[str, Any]) -> MediaAssociation:
    return MediaAssociation(
        MuseumNumber.of(document["fragmentId"]),
        document["sortOrder"],
        document["isPrimary"],
    )


def _import_source_document(import_source: MediaImportSource) -> dict[str, Any]:
    document: dict[str, Any] = {
        "system": import_source.system,
        "fileId": import_source.file_id,
    }
    if import_source.container is not None:
        document["container"] = import_source.container
    return document


def _import_source_of(
    document: Optional[Mapping[str, Any]],
) -> Optional[MediaImportSource]:
    return (
        None
        if document is None
        else MediaImportSource(
            document["system"],
            document["fileId"],
            container=document.get("container"),
        )
    )


def _representations_document(stored: StoredMedia) -> dict[str, Any]:
    representations = stored.media.representations
    handles = stored.representations
    thumbnail_handles = {
        thumbnail.size: thumbnail.handle for thumbnail in handles.thumbnails
    }
    document: dict[str, Any] = {
        "original": _representation_document(
            representations.original, handles.original
        ),
        "thumbnails": {
            size.value: _representation_document(
                representation, thumbnail_handles[size]
            )
            for size, representation in representations.thumbnails
        },
    }
    if representations.display is not None and handles.display is not None:
        document["display"] = _representation_document(
            representations.display, handles.display
        )
    return document


def _thumbnail_documents(
    document: Mapping[str, Any],
) -> Sequence[tuple[ThumbnailSize, Mapping[str, Any]]]:
    thumbnails = document.get("thumbnails") or {}
    return tuple(
        (ThumbnailSize(size), thumbnail) for size, thumbnail in thumbnails.items()
    )


def _media_of(document: Mapping[str, Any]) -> Media:
    representations = document["representations"]
    display = representations.get("display")
    return Media(
        id=MediaId(document["_id"]),
        type=MediaType(document["type"]),
        original_filename=document["originalFilename"],
        representations=MediaRepresentations(
            _representation_of(representations["original"]),
            tuple(
                (size, _representation_of(thumbnail))
                for size, thumbnail in _thumbnail_documents(representations)
            ),
            display=None if display is None else _representation_of(display),
        ),
        associations=tuple(
            _association_of(association) for association in document["associations"]
        ),
        projects=tuple(
            PROJECTS_BY_ABBREVIATION[project]
            for project in document.get("projects") or ()
        ),
        references=tuple(
            MediaReference(reference["id"])
            for reference in document.get("references") or ()
        ),
        caption=document.get("caption"),
        attribution=document.get("attribution"),
        import_source=_import_source_of(document.get("importSource")),
    )


def _stored_representations_of(
    document: Mapping[str, Any],
) -> StoredMediaRepresentations:
    representations = document["representations"]
    display = representations.get("display")
    return StoredMediaRepresentations(
        _handle_of(representations["original"]),
        tuple(
            StoredThumbnailRepresentation(size, _handle_of(thumbnail))
            for size, thumbnail in _thumbnail_documents(representations)
        ),
        display=None if display is None else _handle_of(display),
    )


def stored_media_document(stored: StoredMedia) -> dict[str, Any]:
    media = stored.media
    document: dict[str, Any] = {
        "_id": str(media.id),
        "type": media.type.value,
        "originalFilename": media.original_filename,
        "projects": [project.abbreviation for project in media.projects],
        "associations": [
            _association_document(association) for association in media.associations
        ],
        "references": [
            {"id": reference.bibliography_id} for reference in media.references
        ],
        "representations": _representations_document(stored),
    }
    if media.caption is not None:
        document["caption"] = media.caption
    if media.attribution is not None:
        document["attribution"] = media.attribution
    if media.import_source is not None:
        document["importSource"] = _import_source_document(media.import_source)
    return document


def stored_media_of(document: Mapping[str, Any]) -> StoredMedia:
    return StoredMedia(_media_of(document), _stored_representations_of(document))


def media_of(document: Mapping[str, Any]) -> Media:
    return _media_of(document)
