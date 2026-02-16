from marshmallow import Schema, fields

from ebl.corpus.application.id_schemas import ChapterIdSchema
from ebl.corpus.web.chapter_schemas import ApiLineSchema
from ebl.transliteration.application.line_schemas import (
    TextLineSchema,
    TranslationLineSchema,
)


class ChapterInfoLineSchema(ApiLineSchema):
    translation = fields.List(  # pyre-ignore[15]
        fields.Nested(TranslationLineSchema), load_default=(), allow_none=True
    )


class ChapterInfoSchema(Schema):
    id_ = fields.Nested(ChapterIdSchema, data_key="id")
    text_name = fields.String(data_key="textName")
    siglums = fields.Dict(fields.String(), fields.String())
    matching_lines = fields.Nested(
        ChapterInfoLineSchema, many=True, data_key="matchingLines"
    )
    matching_colophon_lines = fields.Dict(
        fields.String(),
        fields.Nested(TextLineSchema, many=True),
        data_key="matchingColophonLines",
    )


class ChapterInfosPaginationSchema(Schema):
    chapter_infos = fields.Nested(
        ChapterInfoSchema,
        many=True,
        required=True,
        dump_only=True,
        data_key="chapterInfos",
    )
    total_count = fields.Integer(required=True, dump_only=True, data_key="totalCount")
