from typing import Optional, Sequence

import attr

from ebl.media.application.media_dtos import MediaRepresentationDto
from ebl.media.application.media_selection import (
    fragment_media_in_order,
    has_photo,
    primary_media_for,
)
from ebl.media.application.media_urls import (
    fragment_media_thumbnail_url,
    legacy_fragment_thumbnail_url,
)
from ebl.media.domain import Media, MediaType, ThumbnailSize
from ebl.transliteration.domain.museum_number import MuseumNumber


@attr.s(auto_attribs=True, frozen=True)
class MediaSummaryPrimaryDto:
    id: str
    type: MediaType
    thumbnail: Optional[MediaRepresentationDto] = None

    @classmethod
    def of(cls, fragment_id: MuseumNumber, media: Media) -> "MediaSummaryPrimaryDto":
        return cls(
            id=str(media.id),
            type=media.type,
            thumbnail=_small_thumbnail_for(fragment_id, media),
        )


@attr.s(auto_attribs=True, frozen=True)
class MediaSummaryDto:
    count: int
    types: Sequence[MediaType]
    primary: Optional[MediaSummaryPrimaryDto] = None

    @classmethod
    def of(cls, fragment_id: MuseumNumber, media: Sequence[Media]) -> "MediaSummaryDto":
        ordered_media = fragment_media_in_order(fragment_id, media)
        primary = primary_media_for(fragment_id, ordered_media)
        return cls(
            count=len(ordered_media),
            types=tuple(dict.fromkeys(item.type for item in ordered_media)),
            primary=(
                MediaSummaryPrimaryDto.of(fragment_id, primary)
                if primary is not None
                else None
            ),
        )


@attr.s(auto_attribs=True, frozen=True)
class FragmentMediaSummaryDto:
    media_summary: MediaSummaryDto
    has_photo: bool
    thumbnail_path: str

    @classmethod
    def of(
        cls, fragment_id: MuseumNumber, media: Sequence[Media]
    ) -> "FragmentMediaSummaryDto":
        return cls(
            media_summary=MediaSummaryDto.of(fragment_id, media),
            has_photo=has_photo(fragment_id, media),
            thumbnail_path=legacy_fragment_thumbnail_url(
                fragment_id, ThumbnailSize.SMALL
            ),
        )


def _small_thumbnail_for(
    fragment_id: MuseumNumber, media: Media
) -> Optional[MediaRepresentationDto]:
    return next(
        (
            MediaRepresentationDto.of(
                fragment_media_thumbnail_url(fragment_id, media.id, size),
                representation,
            )
            for size, representation in media.representations.thumbnails
            if size is ThumbnailSize.SMALL
        ),
        None,
    )
