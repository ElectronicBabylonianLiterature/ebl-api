from marshmallow import Schema, fields

from ebl.corpus.application.id_schemas import ChapterIdSchema
from ebl.corpus.web.chapter_schemas import ApiLineSchema


class LineSchema(Schema):
    atf = fields.String()


class ChapterInfoSchema(Schema):
    id_ = fields.Nested(ChapterIdSchema, data_key="id")
    siglums = fields.Mapping(fields.String(), fields.String())
    matching_lines = fields.Nested(ApiLineSchema, many=True, data_key="matchingLines")
    matching_colophon_lines = fields.Mapping(
        fields.String(),
        fields.Pluck(LineSchema, "atf", many=True),
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
