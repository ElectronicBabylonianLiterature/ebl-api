from marshmallow import EXCLUDE, Schema, fields, post_load

from ebl.transliteration.application.line_number_schemas import OneOfLineNumberSchema
from ebl.transliteration.application.note_line_part_schemas import (
    OneOfNoteLinePartSchema,
)
from ebl.transliteration.application.token_schemas import OneOfTokenSchema
from ebl.transliteration.domain.labels import LineNumberLabel
from ebl.transliteration.domain.line import ControlLine, EmptyLine
from ebl.transliteration.domain.note_line import NoteLine
from ebl.transliteration.domain.text_line import TextLine


class LineBaseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    prefix = fields.String(required=True)
    content = fields.Nested(OneOfTokenSchema, many=True)


class TextLineSchema(LineBaseSchema):
    line_number = fields.Nested(
        OneOfLineNumberSchema, missing=None, data_key="lineNumber",
    )

    @post_load
    def make_line(self, data, **kwargs):
        return TextLine.of_legacy_iterable(
            LineNumberLabel.from_atf(data["prefix"]),
            data["content"],
            data["line_number"],
        )


class ControlLinesSchema(LineBaseSchema):
    display_value = fields.String(required=True, data_key="displayValue")


class ControlLineSchema(LineBaseSchema):
    @post_load
    def make_line(self, data, **kwargs):
        return ControlLine(data["prefix"], data["content"])


class EmptyLineSchema(LineBaseSchema):
    @post_load
    def make_line(self, data, **kwargs):
        return EmptyLine()


class NoteLineSchema(LineBaseSchema):
    parts = fields.List(fields.Nested(OneOfNoteLinePartSchema), required=True)

    @post_load
    def make_line(self, data, **kwargs):
        return NoteLine(data["parts"])
