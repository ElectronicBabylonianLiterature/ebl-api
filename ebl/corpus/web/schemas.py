from marshmallow import (  # pyre-ignore[21]
    EXCLUDE,
    Schema,
    ValidationError,
    fields,
    post_load,
)
from marshmallow.validate import Regexp  # pyre-ignore[21]

from ebl.bibliography.application.reference_schema import ApiReferenceSchema
from ebl.corpus.application.schemas import (
    ChapterSchema,
    LineSchema,
    ManuscriptSchema,
    TextSchema,
    labels,
    manuscript_id,
)
from ebl.corpus.domain.text import Line, ManuscriptLine
from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.transliteration.application.one_of_line_schema import OneOfLineSchema
from ebl.transliteration.domain.atf_visitor import convert_to_atf
from ebl.transliteration.domain.lark_parser import (
    parse_line_number,
    parse_note_line,
    parse_paratext,
    parse_text_line,
)
from ebl.transliteration.domain.line import EmptyLine
from ebl.transliteration.domain.reconstructed_text_parser import (
    parse_reconstructed_line,
)
from ebl.transliteration.domain.text_line import TextLine
from typing import cast
from lark.exceptions import ParseError, UnexpectedInput  # pyre-ignore[21]


class MuseumNumberString(fields.String):  # pyre-ignore[11]
    def _serialize(self, value, attr, obj, **kwargs):
        return super()._serialize(str(value) if value else "", attr, obj, **kwargs)

    def _deserialize(self, value, attr, data, **kwargs):
        try:
            deserialized = super()._deserialize(value, attr, data, **kwargs)
            return MuseumNumber.of(deserialized) if deserialized else None
        except ValueError as error:
            raise ValidationError("Invalid museum number.") from error


class ApiManuscriptSchema(ManuscriptSchema):
    # pyre-ignore[28]
    museum_number = MuseumNumberString(required=True, data_key="museumNumber")
    references = fields.Nested(ApiReferenceSchema, many=True, required=True)


def _serialize_number(manuscript_line: ManuscriptLine) -> str:
    return (
        cast(TextLine, manuscript_line.line).line_number.label
        if isinstance(manuscript_line.line, TextLine)
        else ""
    )


def _serialize_atf(manuscript_line: ManuscriptLine) -> str:
    return "\n".join(
        [
            manuscript_line.line.atf[
                len(cast(TextLine, manuscript_line.line).line_number.atf) + 1 :
            ]
            if isinstance(manuscript_line.line, TextLine)
            else "",
            *[line.atf for line in manuscript_line.paratext],
        ]
    ).strip()


class ApiManuscriptLineSchema(Schema):  # pyre-ignore[11]
    manuscript_id = manuscript_id()
    labels = labels()
    number = fields.Function(_serialize_number, lambda value: value, required=True)
    atf = fields.Function(_serialize_atf, lambda value: value, required=True)
    atfTokens = fields.Function(
        # pyre-ignore[16]
        lambda manuscript_line: OneOfLineSchema().dump(manuscript_line.line)["content"],
        lambda value: value,
    )

    @post_load  # pyre-ignore[56]
    def make_manuscript_line(self, data: dict, **kwargs) -> ManuscriptLine:
        has_text_line = len(data["number"]) > 0
        lines = data["atf"].split("\n")
        text = (
            parse_text_line(f"{data['number']}. {lines[0]}")
            if has_text_line
            else EmptyLine()
        )
        paratext = lines[1:] if has_text_line else lines
        return ManuscriptLine(
            data["manuscript_id"],
            tuple(data["labels"]),
            text,
            tuple(parse_paratext(line) for line in paratext),
        )


class RecontsructionTokenSchema(Schema):
    type = fields.Function(lambda token: type(token).__name__)
    value = fields.String()


class LineNumberString(fields.String):
    def _serialize(self, value, attr, obj, **kwargs):
        return super()._serialize(value.label, attr, obj, **kwargs)

    def _deserialize(self, value, attr, data, **kwargs):
        try:
            deserialized = super()._deserialize(value, attr, data, **kwargs)
            return parse_line_number(deserialized)
        except (ValueError, ParseError, UnexpectedInput) as error:
            raise ValidationError("Invalid line number.") from error


class ApiLineSchema(LineSchema):
    class Meta:
        exclude = ("text", "note")
        unknown = EXCLUDE

    number = LineNumberString(required=True)  # pyre-ignore[28]
    reconstruction = fields.Function(
        lambda line: "".join(
            [
                convert_to_atf(None, line.reconstruction),
                f"\n{line.note.atf}" if line.note else "",
            ]
        ),
        lambda value: value,
        required=True,
        validate=Regexp(
            r"^[^\n]*(\n[^\n]*)?$", error="Too many note lines in reconstruction."
        ),
    )
    reconstructionTokens = fields.Nested(
        RecontsructionTokenSchema, many=True, attribute="reconstruction", dump_only=True
    )
    manuscripts = fields.Nested(ApiManuscriptLineSchema, many=True, required=True)

    @post_load  # pyre-ignore[56]
    def make_line(self, data: dict, **kwargs) -> Line:
        [text, *notes] = data["reconstruction"].split("\n")
        return Line(
            TextLine.of_iterable(data["number"], parse_reconstructed_line(text)),
            parse_note_line(notes[0]) if notes else None,
            data["is_second_line_of_parallelism"],
            data["is_beginning_of_section"],
            tuple(data["manuscripts"]),
        )


class ApiChapterSchema(ChapterSchema):
    manuscripts = fields.Nested(ApiManuscriptSchema, many=True, required=True)
    lines = fields.Nested(ApiLineSchema, many=True, required=True)


class ApiTextSchema(TextSchema):
    chapters = fields.Nested(ApiChapterSchema, many=True, required=True)
