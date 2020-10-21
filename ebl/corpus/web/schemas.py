from marshmallow import EXCLUDE, Schema, fields, post_load  # pyre-ignore[21]
from marshmallow.validate import Regexp

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
from ebl.transliteration.domain.labels import LineNumberLabel
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


class ApiManuscriptSchema(ManuscriptSchema):
    museum_number = fields.Function(
        lambda manuscript: str(manuscript.museum_number)
        if manuscript.museum_number
        else "",
        lambda value: MuseumNumber.of(value) if value else None,
        required=True,
        data_key="museumNumber",
    )
    references = fields.Nested(ApiReferenceSchema, many=True, required=True)


class ApiManuscriptLineSchema(Schema):  # pyre-ignore[11]
    manuscript_id = manuscript_id()
    labels = labels()
    number = fields.Function(
        lambda manuscript_line: LineNumberLabel.from_atf(
            manuscript_line.line.line_number.atf
        ).to_value()
        if isinstance(manuscript_line.line, TextLine)
        else "",
        lambda value: value,
        required=True,
    )
    atf = fields.Function(
        lambda manuscript_line: "\n".join(
            [
                manuscript_line.line.atf[
                    len(manuscript_line.line.line_number.atf) + 1 :
                ]
                if isinstance(manuscript_line.line, TextLine)
                else "",
                *[line.atf for line in manuscript_line.paratext],
            ]
        ).strip(),
        lambda value: value,
        required=True,
    )
    atfTokens = fields.Function(
        lambda manuscript_line: OneOfLineSchema().dump(manuscript_line.line)["content"],
        lambda value: value,
    )

    @post_load
    def make_manuscript_line(self, data: dict, **kwargs) -> ManuscriptLine:
        has_text_line = len(data["number"]) > 0
        lines = data["atf"].split("\n")
        text = (
            parse_text_line(f"{LineNumberLabel(data['number']).to_atf()} {lines[0]}")
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


class RecontsructionTokenSchema(Schema):  # pyre-ignore[11]
    type = fields.Function(lambda token: type(token).__name__)
    value = fields.String()


class ApiLineSchema(LineSchema):
    class Meta:
        exclude = ("text", "note")
        unknown = EXCLUDE

    number = fields.Function(
        lambda line: LineNumberLabel.from_atf(line.number.atf).to_value(),
        lambda value: parse_line_number(value),
        required=True,
    )
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

    @post_load
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
