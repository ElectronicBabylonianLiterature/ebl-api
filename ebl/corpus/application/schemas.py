from marshmallow import Schema, fields, post_load  # pyre-ignore[21]
from ebl.corpus.domain.text import Chapter, Line, Manuscript, ManuscriptLine, Text
from ebl.fragmentarium.application.museum_number_schema import MuseumNumberSchema
from ebl.transliteration.application.line_schemas import NoteLineSchema, TextLineSchema
from ebl.bibliography.application.reference_schema import ReferenceSchema
from ebl.corpus.domain.enums import (
    Classification,
    ManuscriptType,
    Period,
    PeriodModifier,
    Provenance,
    Stage,
)
from ebl.schemas import ValueEnum
from ebl.transliteration.domain.labels import parse_label
from ebl.transliteration.application.one_of_line_schema import OneOfLineSchema


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
    line = fields.Nested(OneOfLineSchema, required=True)
    paratext = fields.Nested(OneOfLineSchema, many=True, required=True)

    @post_load
    def make_manuscript_line(self, data: dict, **kwargs) -> ManuscriptLine:
        return ManuscriptLine(
            data["manuscript_id"],
            tuple(data["labels"]),
            data["line"],
            tuple(data["paratext"]),
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
