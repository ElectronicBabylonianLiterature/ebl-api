from marshmallow import Schema, fields

from ebl.corpus.application.id_schemas import TextIdSchema
from ebl.corpus.domain.stage import Stage
from ebl.corpus.web.chapter_schemas import ApiLineSchema
from ebl.schemas import ValueEnum


class ChapterIdSchema(Schema):
    text_id = fields.Nested(TextIdSchema, data_key="textId")
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
