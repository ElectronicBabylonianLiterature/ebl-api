from types import MappingProxyType
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
    def of(
        cls, url: str, representation: MediaRepresentation
    ) -> "MediaRepresentationDto":
        return cls(
            url=url,
            mime_type=representation.mime_type,
            width=representation.width,
            height=representation.height,
        )


@attr.s(auto_attribs=True, frozen=True)
class MediaReferenceDto:
    id: str


def _read_only_thumbnails(
    value: Mapping[str, MediaRepresentationDto],
) -> Mapping[str, MediaRepresentationDto]:
    return MappingProxyType(dict(value))


def _references_of(
    value: Sequence[MediaReferenceDto],
) -> tuple[MediaReferenceDto, ...]:
    return tuple(value)


def _media_items_of(
    value: Sequence["FragmentMediaItemDto"],
) -> tuple["FragmentMediaItemDto", ...]:
    return tuple(value)


@attr.s(auto_attribs=True, frozen=True, hash=False)
class MediaRepresentationsDto:
    original: MediaRepresentationDto
    display: Optional[MediaRepresentationDto] = None
    thumbnails: Mapping[str, MediaRepresentationDto] = attr.ib(
        factory=dict, converter=_read_only_thumbnails
    )

    def __hash__(self) -> int:
        return hash(
            (
                self.original,
                self.display,
                tuple(sorted(self.thumbnails.items())),
            )
        )


@attr.s(auto_attribs=True, frozen=True)
class FragmentMediaItemDto:
    id: str
    type: MediaType
    sort_order: int
    is_primary: bool
    representations: MediaRepresentationsDto
    caption: Optional[str] = None
    attribution: Optional[str] = None
    references: Sequence[MediaReferenceDto] = attr.ib(
        factory=tuple, converter=_references_of
    )

    @classmethod
    def of(cls, fragment_id: MuseumNumber, media: Media) -> "FragmentMediaItemDto":
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
                MediaReferenceDto(reference.bibliography_id)
                for reference in media.references
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
    media: Sequence[FragmentMediaItemDto] = attr.ib(converter=_media_items_of)

    @classmethod
    def of(
        cls, fragment_id: MuseumNumber, media: Sequence[Media]
    ) -> "FragmentMediaResponseDto":
        return cls(tuple(FragmentMediaItemDto.of(fragment_id, item) for item in media))
