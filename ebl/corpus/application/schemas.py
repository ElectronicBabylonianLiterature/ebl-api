from marshmallow import Schema, fields, post_load  # pyre-ignore[21]
from ebl.corpus.domain.text import Manuscript
from ebl.fragmentarium.application.museum_number_schema import MuseumNumberSchema
from ebl.bibliography.application.reference_schema import (
    ApiReferenceSchema,
    ReferenceSchema,
)
from ebl.corpus.domain.enums import ManuscriptType, Period, PeriodModifier, Provenance
from ebl.schemas import ValueEnum
from ebl.fragmentarium.domain.museum_number import MuseumNumber


class ManuscriptSchema(Schema):  # pyre-ignore[11]
    id = fields.Integer(required=True)
    siglum_disambiguator = fields.String(required=True, data_key="siglumDisambiguator")
    museum_number = fields.Function(
        lambda manuscript: manuscript.museum_number
        and MuseumNumberSchema().dump(manuscript.museum_number),
        lambda value: None
        if not value
        else (
            MuseumNumber.of(value)
            if isinstance(value, str)
            else MuseumNumberSchema().load(value)
        ),
        required=True,
        allow_none=True,
        data_key="museumNumber",
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
    def make_manuscript(self, data, **kwargs) -> Manuscript:
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
