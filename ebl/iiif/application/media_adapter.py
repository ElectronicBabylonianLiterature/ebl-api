from typing import List, Optional, Sequence

from ebl.common.domain.project import ResearchProject
from ebl.common.domain.scopes import Scope
from ebl.iiif.application.manifest_sources import (
    FragmentSource,
    ImageSource,
    MediaSource,
    MetadataSource,
    RenderingSource,
)
from ebl.iiif.domain.image_formats import is_paintable
from ebl.media.application.media_urls import (
    fragment_media_display_url,
    fragment_media_original_url,
    fragment_media_thumbnail_url,
)
from ebl.media.domain import Media, MediaRepresentation, ThumbnailSize
from ebl.transliteration.domain.museum_number import MuseumNumber

PROJECT_LABEL = "Project"
REFERENCE_LABEL = "Reference"
THUMBNAIL_PREFERENCE = (
    ThumbnailSize.SMALL,
    ThumbnailSize.MEDIUM,
    ThumbnailSize.LARGE,
)


def _image_source(url: str, representation: MediaRepresentation) -> ImageSource:
    return ImageSource(
        url=url,
        mime_type=representation.mime_type,
        width=representation.width,
        height=representation.height,
    )


def _painting_image(fragment_id: MuseumNumber, media: Media) -> Optional[ImageSource]:
    display = media.representations.display
    if display is not None and is_paintable(display.mime_type):
        return _image_source(fragment_media_display_url(fragment_id, media.id), display)

    original = media.representations.original
    if is_paintable(original.mime_type):
        return _image_source(
            fragment_media_original_url(fragment_id, media.id), original
        )

    return None


def _thumbnail_image(fragment_id: MuseumNumber, media: Media) -> Optional[ImageSource]:
    thumbnails = dict(media.representations.thumbnails)
    for size in THUMBNAIL_PREFERENCE:
        representation = thumbnails.get(size)
        if representation is not None and is_paintable(representation.mime_type):
            return _image_source(
                fragment_media_thumbnail_url(fragment_id, media.id, size),
                representation,
            )

    return None


def _rendering(fragment_id: MuseumNumber, media: Media) -> Optional[RenderingSource]:
    original = media.representations.original
    if is_paintable(original.mime_type):
        return None

    return RenderingSource(
        url=fragment_media_original_url(fragment_id, media.id),
        mime_type=original.mime_type,
        label=media.original_filename,
    )


def media_source_of(fragment_id: MuseumNumber, media: Media) -> MediaSource:
    association = media.association_for(fragment_id)
    original = media.representations.original
    return MediaSource(
        media_id=str(media.id),
        sort_order=association.sort_order,
        canvas_width=original.width,
        canvas_height=original.height,
        painting_image=_painting_image(fragment_id, media),
        thumbnail_image=_thumbnail_image(fragment_id, media),
        rendering=_rendering(fragment_id, media),
        label=media.caption,
        attribution=media.attribution,
        is_primary=association.is_primary,
    )


def _distinct_projects(
    media_items: Sequence[Media],
) -> Sequence[ResearchProject]:
    projects: List[ResearchProject] = []
    for media in media_items:
        for project in media.projects:
            if project not in projects:
                projects.append(project)

    return tuple(projects)


def _distinct_bibliography_ids(media_items: Sequence[Media]) -> Sequence[str]:
    bibliography_ids: List[str] = []
    for media in media_items:
        for reference in media.references:
            if reference.bibliography_id not in bibliography_ids:
                bibliography_ids.append(reference.bibliography_id)

    return tuple(bibliography_ids)


def media_metadata_of(media_items: Sequence[Media]) -> Sequence[MetadataSource]:
    projects = [
        MetadataSource(label=PROJECT_LABEL, value=project.long_name)
        for project in _distinct_projects(media_items)
    ]
    references = [
        MetadataSource(label=REFERENCE_LABEL, value=bibliography_id)
        for bibliography_id in _distinct_bibliography_ids(media_items)
    ]
    return tuple(projects + references)


def fragment_source_of(
    number: MuseumNumber,
    media_items: Sequence[Media],
    authorized_scopes: Sequence[Scope] = (),
    summary: Optional[str] = None,
    homepage_url: Optional[str] = None,
    record_url: Optional[str] = None,
) -> FragmentSource:
    associated = tuple(
        media for media in media_items if media.is_associated_with(number)
    )
    return FragmentSource(
        number=number,
        authorized_scopes=tuple(authorized_scopes),
        media=tuple(media_source_of(number, media) for media in associated),
        metadata=media_metadata_of(associated),
        summary=summary,
        homepage_url=homepage_url,
        record_url=record_url,
    )
