from typing import Optional, Sequence

import attr

from ebl.media.application.media_dtos import MediaRepresentationDto
from ebl.media.application.media_urls import (
    fragment_media_thumbnail_url,
    fragment_thumbnail_url,
)
from ebl.media.domain import Media, MediaType, ThumbnailSize
from ebl.transliteration.domain.museum_number import MuseumNumber


@attr.s(auto_attribs=True, frozen=True)
class MediaSummaryPrimaryDto:
    id: str
    type: MediaType
    thumbnail: Optional[MediaRepresentationDto] = None


@attr.s(auto_attribs=True, frozen=True)
class MediaSummaryDto:
    count: int
    types: Sequence[MediaType]
    primary: Optional[MediaSummaryPrimaryDto] = None


@attr.s(auto_attribs=True, frozen=True)
class FragmentMediaSummaryDto:
    media_summary: MediaSummaryDto
    has_photo: bool
    thumbnail_path: Optional[str] = None

    @classmethod
    def of(cls, fragment_id: MuseumNumber, media: Sequence[Media]):
        ordered_media = tuple(
            sorted(media, key=lambda item: _sort_key(fragment_id, item))
        )
        has_photo = any(item.type is MediaType.PHOTO for item in ordered_media)
        primary = _primary_media_for(fragment_id, ordered_media)
        primary_thumbnail = (
            _small_thumbnail_for(fragment_id, primary) if primary is not None else None
        )
        thumbnail_photo = _photo_with_small_thumbnail_for(fragment_id, ordered_media)
        thumbnail_path = (
            fragment_thumbnail_url(fragment_id, ThumbnailSize.SMALL)
            if thumbnail_photo is not None
            else None
        )
        return cls(
            media_summary=MediaSummaryDto(
                count=len(ordered_media),
                types=tuple(dict.fromkeys(item.type for item in ordered_media)),
                primary=(
                    MediaSummaryPrimaryDto(
                        id=str(primary.id),
                        type=primary.type,
                        thumbnail=primary_thumbnail,
                    )
                    if primary is not None
                    else None
                ),
            ),
            has_photo=has_photo,
            thumbnail_path=thumbnail_path,
        )


def _primary_media_for(
    fragment_id: MuseumNumber, media: Sequence[Media]
) -> Optional[Media]:
    primary_items = [
        item for item in media if item.association_for(fragment_id).is_primary
    ]
    return next(
        (item for item in primary_items if item.type is MediaType.PHOTO),
        primary_items[0] if primary_items else None,
    )


def _sort_key(fragment_id: MuseumNumber, media: Media) -> tuple[int, str]:
    return media.association_for(fragment_id).sort_order, str(media.id)


def _photo_with_small_thumbnail_for(
    fragment_id: MuseumNumber, media: Sequence[Media]
) -> Optional[Media]:
    return next(
        (
            item
            for item in media
            if item.type is MediaType.PHOTO
            and _small_thumbnail_for(fragment_id, item) is not None
        ),
        None,
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
