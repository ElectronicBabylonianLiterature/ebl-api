from marshmallow import EXCLUDE, Schema, fields, post_load

from ebl.transliteration.application.label_schemas import labels
from ebl.transliteration.application.line_number_schemas import OneOfLineNumberSchema
from ebl.transliteration.application.note_line_part_schemas import (
    OneOfNoteLinePartSchema,
)
from ebl.transliteration.application.token_schemas import OneOfTokenSchema
from ebl.transliteration.domain.line import ControlLine, EmptyLine
from ebl.transliteration.domain.note_line import NoteLine
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import ValueToken
from ebl.transliteration.domain.translation_line import Extent, TranslationLine


class LineBaseSchema(Schema):
    class Meta:
        unknown = EXCLUDE


class TextLineSchema(LineBaseSchema):
    prefix = fields.Function(lambda obj: obj.line_number.atf, lambda value: value)
    content = fields.Nested(OneOfTokenSchema, many=True, required=True)
    line_number = fields.Nested(
        OneOfLineNumberSchema, required=True, data_key="lineNumber"
    )

    @post_load
    def make_line(self, data, **kwargs) -> TextLine:
        return TextLine.of_iterable(data["line_number"], data["content"])


class ControlLineSchema(LineBaseSchema):
    prefix = fields.String(required=True)
    content = fields.Function(
        lambda obj: [OneOfTokenSchema().dump(ValueToken.of(obj.content))],
        lambda value: OneOfTokenSchema().load(value, many=True),
        required=True,
    )

    @post_load
    def make_line(self, data, **kwargs) -> ControlLine:
        return ControlLine(
            data["prefix"], " ".join(token.value for token in data["content"])
        )


class EmptyLineSchema(LineBaseSchema):
    prefix = fields.Constant("")
    content = fields.Constant([])

    @post_load
    def make_line(self, data, **kwargs) -> EmptyLine:
        return EmptyLine()


class NoteLineSchema(LineBaseSchema):
    prefix = fields.Constant("#note: ")
    content = fields.Function(
        lambda obj: OneOfTokenSchema().dump(
            [ValueToken.of(part.value) for part in obj.parts], many=True
        ),
        lambda value: value,
    )
    parts = fields.List(fields.Nested(OneOfNoteLinePartSchema), required=True)

    @post_load
    def make_line(self, data, **kwargs) -> NoteLine:
        return NoteLine(data["parts"])


class ExtentSchema(Schema):
    number = fields.Nested(OneOfLineNumberSchema, required=True)
    labels = labels()

    @post_load
    def make_extent(self, data, **kwargs) -> Extent:
        return Extent(data["number"], data["labels"])


class TranslationLineSchema(LineBaseSchema):
    prefix = fields.String()
    content = fields.Function(
        lambda obj: [
            OneOfTokenSchema().dump(
                ValueToken.of("".join(part.value for part in obj.parts))
            )
        ],
        lambda value: value,
    )

    parts = fields.List(fields.Nested(OneOfNoteLinePartSchema), required=True)
    language = fields.String(required=True)
    extent = fields.Nested(ExtentSchema, required=True, allow_none=True)

    @post_load
    def make_line(self, data, **kwargs) -> TranslationLine:
        return TranslationLine(data["parts"], data["language"], data["extent"])
