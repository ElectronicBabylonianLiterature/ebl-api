from marshmallow import Schema, fields, post_load  # pyre-ignore[21]
from ebl.corpus.domain.text import Line, Manuscript, ManuscriptLine
from ebl.fragmentarium.application.museum_number_schema import MuseumNumberSchema
from ebl.transliteration.application.line_schemas import TextLineSchema
from ebl.bibliography.application.reference_schema import (
    ApiReferenceSchema,
    ReferenceSchema,
)
from ebl.corpus.domain.enums import ManuscriptType, Period, PeriodModifier, Provenance
from ebl.schemas import ValueEnum
from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.transliteration.domain.labels import LineNumberLabel, parse_label
from ebl.transliteration.domain.lark_parser import parse_line, parse_line_number
from typing import cast
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.application.line_number_schemas import OneOfLineNumberSchema
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
    number = fields.Nested(OneOfLineNumberSchema, required=True)
    reconstruction = fields.Function(
        lambda line: convert_to_atf(None, line.reconstruction),
        lambda value: parse_reconstructed_line(value),
        required=True,
    )
    is_second_line_of_parallelism = fields.Boolean(
        missing=False, data_key="isSecondLineOfParallelism"
    )
    is_beginning_of_section = fields.Boolean(
        missing=False, data_key="isBeginningOfSection"
    )
    manuscripts = fields.Nested(ManuscriptLineSchema, many=True, required=True)

    @post_load
    def make_line(self, data: dict, **kwargs) -> Line:
        return Line(
            data["number"],
            data["reconstruction"],
            data["is_second_line_of_parallelism"],
            data["is_beginning_of_section"],
            tuple(data["manuscripts"]),
        )


class RecontsructionTokenSchema(Schema):  # pyre-ignore[11]
    type = fields.Function(lambda token: type(token).__name__)
    value = fields.String()


class ApiLineSchema(LineSchema):
    number = fields.Function(
        lambda line: LineNumberLabel.from_atf(line.number.atf).to_value(),
        lambda value: parse_line_number(value),
    )
    reconstructionTokens = fields.Nested(
        RecontsructionTokenSchema, many=True, attribute="reconstruction", dump_only=True
    )
    manuscripts = fields.Nested(ApiManuscriptLineSchema, many=True, required=True)
