from typing import Mapping, Optional, Sequence

import attr

from ebl.media.application.media_urls import (
    fragment_media_display_url,
    fragment_media_original_url,
    fragment_media_thumbnail_url,
)
from ebl.media.domain import Media, MediaRepresentation, MediaType
from ebl.transliteration.domain.museum_number import MuseumNumber


@attr.s(auto_attribs=True, frozen=True)
class MediaRepresentationDto:
    url: str
    mime_type: str
    width: int
    height: int

    @classmethod
    def of(cls, url: str, representation: MediaRepresentation):
        return cls(
            url=url,
            mime_type=representation.mime_type,
            width=representation.width,
            height=representation.height,
        )


@attr.s(auto_attribs=True, frozen=True)
class MediaReferenceDto:
    id: str


@attr.s(auto_attribs=True, frozen=True)
class MediaRepresentationsDto:
    original: MediaRepresentationDto
    display: Optional[MediaRepresentationDto] = None
    thumbnails: Mapping[str, MediaRepresentationDto] = attr.ib(factory=dict)


@attr.s(auto_attribs=True, frozen=True)
class FragmentMediaItemDto:
    id: str
    type: MediaType
    sort_order: int
    is_primary: bool
    representations: MediaRepresentationsDto
    caption: Optional[str] = None
    attribution: Optional[str] = None
    references: Sequence[MediaReferenceDto] = ()

    @classmethod
    def of(cls, fragment_id: MuseumNumber, media: Media):
        association = media.association_for(fragment_id)
        display_representation = media.representations.display
        return cls(
            id=str(media.id),
            type=media.type,
            sort_order=association.sort_order,
            is_primary=association.is_primary,
            caption=media.caption,
            attribution=media.attribution,
            references=tuple(
                MediaReferenceDto(reference.id) for reference in media.references
            ),
            representations=MediaRepresentationsDto(
                original=MediaRepresentationDto.of(
                    fragment_media_original_url(fragment_id, media.id),
                    media.representations.original,
                ),
                display=(
                    MediaRepresentationDto.of(
                        fragment_media_display_url(fragment_id, media.id),
                        display_representation,
                    )
                    if display_representation is not None
                    else None
                ),
                thumbnails={
                    size.value: MediaRepresentationDto.of(
                        fragment_media_thumbnail_url(fragment_id, media.id, size),
                        representation,
                    )
                    for size, representation in media.representations.thumbnails
                },
            ),
        )


@attr.s(auto_attribs=True, frozen=True)
class FragmentMediaResponseDto:
    media: Sequence[FragmentMediaItemDto]

    @classmethod
    def of(cls, fragment_id: MuseumNumber, media: Sequence[Media]):
        return cls(tuple(FragmentMediaItemDto.of(fragment_id, item) for item in media))
