from marshmallow import Schema, fields

from ebl.corpus.application.id_schemas import TextIdSchema
from ebl.schemas import ValueEnum
from ebl.corpus.domain.chapter import Classification
from ebl.corpus.domain.stage import Stage
from ebl.corpus.web.text_schemas import ApiLineSchema


class ChapterIdSchema(Schema):
    classification = ValueEnum(Classification)
    stage = ValueEnum(Stage)
    name = fields.String()


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


class TextInfoSchema(Schema):
    id_ = fields.Nested(TextIdSchema, data_key="id")
    matching_chapters = fields.Nested(
        ChapterInfoSchema, many=True, data_key="matchingChapters"
    )
