from marshmallow import Schema, EXCLUDE, fields, post_load  # pyre-ignore[21]
from marshmallow.validate import Regexp
from ebl.corpus.domain.text import Chapter, Line, Manuscript, ManuscriptLine, Text
from ebl.fragmentarium.application.museum_number_schema import MuseumNumberSchema
from ebl.transliteration.application.line_schemas import NoteLineSchema, TextLineSchema
from ebl.bibliography.application.reference_schema import (
    ApiReferenceSchema,
    ReferenceSchema,
)
from ebl.corpus.domain.enums import (
    Classification,
    ManuscriptType,
    Period,
    PeriodModifier,
    Provenance,
    Stage,
)
from ebl.schemas import ValueEnum
from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.transliteration.domain.labels import LineNumberLabel, parse_label
from ebl.transliteration.domain.lark_parser import (
    parse_line,
    parse_line_number,
    parse_note_line,
)
from typing import cast
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.atf_visitor import convert_to_atf
from ebl.transliteration.domain.reconstructed_text_parser import (
    parse_reconstructed_line,
)


class ManuscriptSchema(Schema):  # pyre-ignore[11]
    id = fields.Integer(required=True)
    siglum_disambiguator = fields.String(required=True, data_key="siglumDisambiguator")
    museum_number = fields.Nested(
        MuseumNumberSchema, required=True, allow_none=True, data_key="museumNumber"
    )
    accession = fields.String(required=True)
    period_modifier = ValueEnum(
        PeriodModifier, required=True, data_key="periodModifier"
    )
    period = fields.Function(
        lambda manuscript: manuscript.period.long_name,
        lambda value: Period.from_name(value),
        required=True,
    )
    provenance = fields.Function(
        lambda manuscript: manuscript.provenance.long_name,
        lambda value: Provenance.from_name(value),
        required=True,
    )
    type = fields.Function(
        lambda manuscript: manuscript.type.long_name,
        lambda value: ManuscriptType.from_name(value),
        required=True,
    )
    notes = fields.String(required=True)
    references = fields.Nested(ReferenceSchema, many=True, required=True)

    @post_load
    def make_manuscript(self, data: dict, **kwargs) -> Manuscript:
        return Manuscript(
            data["id"],
            data["siglum_disambiguator"],
            data["museum_number"],
            data["accession"],
            data["period_modifier"],
            data["period"],
            data["provenance"],
            data["type"],
            data["notes"],
            tuple(data["references"]),
        )


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


def manuscript_id():
    return fields.Integer(required=True, data_key="manuscriptId")


def labels():
    return fields.Function(
        lambda manuscript_line: [label.to_value() for label in manuscript_line.labels],
        lambda value: [parse_label(label) for label in value],
        required=True,
    )


class ManuscriptLineSchema(Schema):  # pyre-ignore[11]
    manuscript_id = manuscript_id()
    labels = labels()
    line = fields.Nested(TextLineSchema, required=True)

    @post_load
    def make_manuscript_line(self, data: dict, **kwargs) -> ManuscriptLine:
        return ManuscriptLine(
            data["manuscript_id"], tuple(data["labels"]), data["line"]
        )


class ApiManuscriptLineSchema(Schema):  # pyre-ignore[11]
    manuscript_id = manuscript_id()
    labels = labels()
    number = fields.Function(
        lambda manuscript_line: LineNumberLabel.from_atf(
            manuscript_line.line.line_number.atf
        ).to_value(),
        lambda value: LineNumberLabel(value).to_atf(),
        required=True,
    )
    atf = fields.Function(
        lambda manuscript_line: manuscript_line.line.atf[
            len(manuscript_line.line.line_number.atf) + 1 :
        ],
        lambda value: value,
        required=True,
    )
    atfTokens = fields.Function(
        lambda manuscript_line: TextLineSchema().dump(manuscript_line.line)["content"],
        lambda value: value,
    )

    @post_load
    def make_manuscript_line(self, data: dict, **kwargs) -> ManuscriptLine:
        return ManuscriptLine(
            data["manuscript_id"],
            tuple(data["labels"]),
            cast(TextLine, parse_line(f"{data['number']} {data['atf']}")),
        )


class LineSchema(Schema):  # pyre-ignore[11]
    text = fields.Nested(TextLineSchema, required=True)
    note = fields.Nested(NoteLineSchema, required=True, allow_none=True)
    is_second_line_of_parallelism = fields.Boolean(
        required=True, data_key="isSecondLineOfParallelism"
    )
    is_beginning_of_section = fields.Boolean(
        required=True, data_key="isBeginningOfSection"
    )
    manuscripts = fields.Nested(ManuscriptLineSchema, many=True, required=True)

    @post_load
    def make_line(self, data: dict, **kwargs) -> Line:
        return Line(
            data["text"],
            data["note"],
            data["is_second_line_of_parallelism"],
            data["is_beginning_of_section"],
            tuple(data["manuscripts"]),
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


class ChapterSchema(Schema):  # pyre-ignore[11]
    classification = ValueEnum(Classification, required=True)
    stage = ValueEnum(Stage, required=True)
    version = fields.String(required=True)
    name = fields.String(required=True)
    order = fields.Integer(required=True)
    manuscripts = fields.Nested(ManuscriptSchema, many=True, required=True)
    lines = fields.Nested(LineSchema, many=True, required=True)
    parser_version = fields.String(missing="", data_key="parserVersion")

    @post_load
    def make_chapter(self, data: dict, **kwargs) -> Chapter:
        return Chapter(
            Classification(data["classification"]),
            Stage(data["stage"]),
            data["version"],
            data["name"],
            data["order"],
            tuple(data["manuscripts"]),
            tuple(data["lines"]),
            data["parser_version"],
        )


class ApiChapterSchema(ChapterSchema):
    manuscripts = fields.Nested(ApiManuscriptSchema, many=True, required=True)
    lines = fields.Nested(ApiLineSchema, many=True, required=True)


class TextSchema(Schema):  # pyre-ignore[11]
    category = fields.Integer(required=True)
    index = fields.Integer(required=True)
    name = fields.String(required=True)
    number_of_verses = fields.Integer(required=True, data_key="numberOfVerses")
    approximate_verses = fields.Boolean(required=True, data_key="approximateVerses")
    chapters = fields.Nested(ChapterSchema, many=True, required=True)

    @post_load
    def make_text(self, data: dict, **kwargs) -> Text:
        return Text(
            data["category"],
            data["index"],
            data["name"],
            data["number_of_verses"],
            data["approximate_verses"],
            tuple(data["chapters"]),
        )


class ApiTextSchema(TextSchema):
    chapters = fields.Nested(ApiChapterSchema, many=True, required=True)
