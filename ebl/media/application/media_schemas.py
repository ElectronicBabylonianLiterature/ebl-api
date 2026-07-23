from typing import FrozenSet

from marshmallow import Schema, fields, post_dump

from ebl.media.application.media_dtos import (
    FragmentMediaItemDto,
    FragmentMediaResponseDto,
    MediaReferenceDto,
    MediaRepresentationDto,
    MediaRepresentationsDto,
)
from ebl.media.application.media_summary_dtos import (
    FragmentMediaSummaryDto,
    MediaSummaryDto,
    MediaSummaryPrimaryDto,
)
from ebl.media.domain import MediaType
from ebl.schemas import NameEnumField


class OmitEmptyMixin:
    preserve_empty_collections: FrozenSet[str] = frozenset()

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
    preserve_empty_collections: FrozenSet[str] = frozenset({"types"})

    count = fields.Integer(required=True)
    types = fields.List(NameEnumField(MediaType), required=True)
    primary = fields.Nested(MediaSummaryPrimaryDtoSchema)


class FragmentMediaSummaryDtoSchema(OmitEmptyMixin, Schema):
    media_summary = fields.Nested(
        MediaSummaryDtoSchema, required=True, data_key="mediaSummary"
    )
    has_photo = fields.Boolean(required=True, data_key="hasPhoto")
    thumbnail_path = fields.String(data_key="thumbnailPath")


__all__ = [
    "FragmentMediaItemDto",
    "FragmentMediaItemDtoSchema",
    "FragmentMediaResponseDto",
    "FragmentMediaResponseDtoSchema",
    "FragmentMediaSummaryDto",
    "FragmentMediaSummaryDtoSchema",
    "MediaReferenceDto",
    "MediaReferenceDtoSchema",
    "MediaRepresentationDto",
    "MediaRepresentationDtoSchema",
    "MediaRepresentationsDto",
    "MediaRepresentationsDtoSchema",
    "MediaSummaryDto",
    "MediaSummaryDtoSchema",
    "MediaSummaryPrimaryDto",
    "MediaSummaryPrimaryDtoSchema",
]
