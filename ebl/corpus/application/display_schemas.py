from marshmallow import Schema, fields, post_load

from ebl.corpus.application.id_schemas import ChapterIdSchema
from ebl.corpus.domain.chapter_display import ChapterDisplay, LineDisplay
from ebl.transliteration.application.line_number_schemas import OneOfLineNumberSchema
from ebl.transliteration.application.note_line_part_schemas import (
    OneOfNoteLinePartSchema,
)
from ebl.transliteration.application.token_schemas import OneOfTokenSchema


class LineDisplaySchema(Schema):
    number = fields.Nested(OneOfLineNumberSchema, required=True)
    reconstruction = fields.List(fields.Nested(OneOfTokenSchema), required=True)
    translation = fields.List(fields.Nested(OneOfNoteLinePartSchema), required=True)

    @post_load
    def make_line(self, data: dict, **kwargs) -> LineDisplay:
        return LineDisplay(
            data["number"],
            tuple(data["reconstruction"]),
            tuple(data["translation"]),
        )


class ChapterDisplaySchema(Schema):
    id_ = fields.Nested(ChapterIdSchema, required=True, data_key="id")
    text_name = fields.String(required=True, data_key="textName")
    lines = fields.Nested(LineDisplaySchema, many=True, required=True)

    @post_load
    def make_chapter(self, data: dict, **kwargs) -> ChapterDisplay:
        return ChapterDisplay(
            data["id_"],
            data["text_name"],
            tuple(data["lines"]),
        )
