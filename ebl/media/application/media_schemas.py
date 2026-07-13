from typing import Mapping, Optional, Sequence

import attr
from marshmallow import Schema, fields, post_dump

from ebl.media.domain import (
    Media,
    MediaRepresentation,
    MediaType,
    ThumbnailSize,
)
from ebl.media.application.media_urls import (
    fragment_media_display_url,
    fragment_media_original_url,
    fragment_media_thumbnail_url,
    fragment_thumbnail_url,
)
from ebl.schemas import NameEnumField
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
            sorted(media, key=lambda item: item.association_for(fragment_id).sort_order)
        )
        has_photo = any(item.type is MediaType.PHOTO for item in ordered_media)
        primary = _primary_media_for(fragment_id, ordered_media)
        primary_thumbnail = (
            _small_thumbnail_for(fragment_id, primary) if primary is not None else None
        )
        primary_photo_thumbnail_path = (
            fragment_thumbnail_url(fragment_id, ThumbnailSize.SMALL)
            if primary is not None
            and primary.type is MediaType.PHOTO
            and primary_thumbnail is not None
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
            thumbnail_path=primary_photo_thumbnail_path,
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


class OmitEmptyMixin:
    preserve_empty_collections = frozenset()

    @post_dump
    def omit_empty(self, data, **kwargs):
        return {
            key: value
            for key, value in data.items()
            if key in self.preserve_empty_collections
            or (value is not None and value != [] and value != {})
        }


class MediaRepresentationDtoSchema(Schema):
    url = fields.String(required=True)
    mime_type = fields.String(required=True, data_key="mimeType")
    width = fields.Integer(required=True)
    height = fields.Integer(required=True)


class MediaReferenceDtoSchema(Schema):
    id = fields.String(required=True)


class MediaRepresentationsDtoSchema(OmitEmptyMixin, Schema):
    original = fields.Nested(MediaRepresentationDtoSchema, required=True)
    display = fields.Nested(MediaRepresentationDtoSchema)
    thumbnails = fields.Dict(
        keys=fields.String(),
        values=fields.Nested(MediaRepresentationDtoSchema),
        required=True,
    )


class FragmentMediaItemDtoSchema(OmitEmptyMixin, Schema):
    id = fields.String(required=True)
    type = NameEnumField(MediaType, required=True)
    sort_order = fields.Integer(required=True, data_key="sortOrder")
    is_primary = fields.Boolean(required=True, data_key="isPrimary")
    caption = fields.String()
    attribution = fields.String()
    references = fields.List(fields.Nested(MediaReferenceDtoSchema))
    representations = fields.Nested(MediaRepresentationsDtoSchema, required=True)


class FragmentMediaResponseDtoSchema(Schema):
    media = fields.List(fields.Nested(FragmentMediaItemDtoSchema), required=True)


class MediaSummaryPrimaryDtoSchema(OmitEmptyMixin, Schema):
    id = fields.String(required=True)
    type = NameEnumField(MediaType, required=True)
    thumbnail = fields.Nested(MediaRepresentationDtoSchema)


class MediaSummaryDtoSchema(OmitEmptyMixin, Schema):
    preserve_empty_collections = frozenset({"types"})

    count = fields.Integer(required=True)
    types = fields.List(NameEnumField(MediaType), required=True)
    primary = fields.Nested(MediaSummaryPrimaryDtoSchema)


class FragmentMediaSummaryDtoSchema(OmitEmptyMixin, Schema):
    media_summary = fields.Nested(
        MediaSummaryDtoSchema, required=True, data_key="mediaSummary"
    )
    has_photo = fields.Boolean(required=True, data_key="hasPhoto")
    thumbnail_path = fields.String(data_key="thumbnailPath")
