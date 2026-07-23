from typing import Sequence

from ebl.common.domain.project import ResearchProject
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

DEFAULT_MEDIA_ID = "550e8400-e29b-41d4-a716-446655440000"
DEFAULT_COPY_MEDIA_ID = "550e8400-e29b-41d4-a716-446655440001"
SECOND_PHOTO_MEDIA_ID = "550e8400-e29b-41d4-a716-446655440002"
SHA256_VALUE = "a" * 64


def media_id(value: str = DEFAULT_MEDIA_ID) -> MediaId:
    return MediaId(value)


def checksum(*, algorithm: str = "sha256", value: str = SHA256_VALUE) -> MediaChecksum:
    return MediaChecksum(algorithm=algorithm, value=value)


def original_representation(mime_type: str = "image/jpeg") -> MediaRepresentation:
    return MediaRepresentation(mime_type, 4000, 3000, 5242880, checksum())


def display_representation(mime_type: str = "image/jpeg") -> MediaRepresentation:
    return MediaRepresentation(mime_type, 2560, 1920, 1179648)


def thumbnail_representation(mime_type: str = "image/jpeg") -> MediaRepresentation:
    return MediaRepresentation(mime_type, 240, 180, 15360)


def medium_thumbnail_representation(
    mime_type: str = "image/jpeg",
) -> MediaRepresentation:
    return MediaRepresentation(mime_type, 480, 360, 61440)


def large_thumbnail_representation(
    mime_type: str = "image/jpeg",
) -> MediaRepresentation:
    return MediaRepresentation(mime_type, 960, 720, 245760)


def representations(
    *,
    original_mime_type: str = "image/jpeg",
    thumbnails: Sequence[tuple[ThumbnailSize, MediaRepresentation]] | None = None,
    display: MediaRepresentation | None = None,
    display_mime_type: str | None = None,
) -> MediaRepresentations:
    return MediaRepresentations(
        original_representation(original_mime_type),
        (
            tuple(thumbnails)
            if thumbnails is not None
            else ((ThumbnailSize.SMALL, thumbnail_representation()),)
        ),
        display=display
        if display is not None
        else (
            display_representation(display_mime_type)
            if display_mime_type is not None
            else None
        ),
    )


def association(
    *,
    fragment_id: str | MuseumNumber = "K.1",
    sort_order: int = 0,
    is_primary: bool = True,
) -> MediaAssociation:
    normalized_fragment_id = (
        fragment_id
        if isinstance(fragment_id, MuseumNumber)
        else MuseumNumber.of(fragment_id)
    )
    return MediaAssociation(normalized_fragment_id, sort_order, is_primary)


def media_reference(reference_id: str = "bibliography-id") -> MediaReference:
    return MediaReference(reference_id)


def media_import_source(
    *,
    system: str = "legacy-gridfs",
    bucket: str = "photos",
    file_id: str = "legacy-gridfs-id",
) -> MediaImportSource:
    return MediaImportSource(system, bucket, file_id)


def media(
    *,
    media_id_: str | MediaId = DEFAULT_MEDIA_ID,
    media_type: MediaType = MediaType.PHOTO,
    original_filename: str = "BM-12345-obverse.jpg",
    media_representations: MediaRepresentations | None = None,
    associations: Sequence[MediaAssociation] | None = None,
    projects: Sequence[ResearchProject] = (),
    references: Sequence[MediaReference] = (),
    caption: str | None = None,
    attribution: str | None = None,
    import_source: MediaImportSource | None = None,
) -> Media:
    normalized_media_id = (
        media_id_ if isinstance(media_id_, MediaId) else MediaId(media_id_)
    )
    return Media(
        id=normalized_media_id,
        type=media_type,
        original_filename=original_filename,
        representations=media_representations or representations(),
        associations=associations if associations is not None else (association(),),
        projects=tuple(projects),
        references=tuple(references),
        caption=caption,
        attribution=attribution,
        import_source=import_source,
    )


def photo_media(**kwargs) -> Media:
    return media(media_type=MediaType.PHOTO, **kwargs)


def copy_media(**kwargs) -> Media:
    return media(
        media_id_=kwargs.pop("media_id_", DEFAULT_COPY_MEDIA_ID),
        media_type=MediaType.COPY,
        **kwargs,
    )
