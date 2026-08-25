from typing import Optional, Sequence

from ebl.media.domain import Media, MediaType
from ebl.transliteration.domain.museum_number import MuseumNumber


def fragment_media_in_order(
    fragment_id: MuseumNumber, media: Sequence[Media]
) -> Sequence[Media]:
    return tuple(sorted(media, key=lambda item: _sort_key(fragment_id, item)))


def primary_photo_for(
    fragment_id: MuseumNumber, media: Sequence[Media]
) -> Optional[Media]:
    return _first_primary(fragment_id, media, MediaType.PHOTO)


def primary_media_for(
    fragment_id: MuseumNumber, media: Sequence[Media]
) -> Optional[Media]:
    photo = primary_photo_for(fragment_id, media)
    return photo if photo is not None else _first_primary(fragment_id, media, None)


def has_photo(fragment_id: MuseumNumber, media: Sequence[Media]) -> bool:
    fragment_types = tuple(_fragment_media_type(fragment_id, item) for item in media)
    return MediaType.PHOTO in fragment_types


def _first_primary(
    fragment_id: MuseumNumber,
    media: Sequence[Media],
    media_type: Optional[MediaType],
) -> Optional[Media]:
    return next(
        (
            item
            for item in fragment_media_in_order(fragment_id, media)
            if item.association_for(fragment_id).is_primary
            and (media_type is None or item.type is media_type)
        ),
        None,
    )


def _fragment_media_type(fragment_id: MuseumNumber, media: Media) -> MediaType:
    media.association_for(fragment_id)
    return media.type


def _sort_key(fragment_id: MuseumNumber, media: Media) -> tuple[int, str]:
    association = media.association_for(fragment_id)
    return association.sort_order, str(media.id)
