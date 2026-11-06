from typing import Any, cast

from marshmallow import Schema, ValidationError, fields, post_load, validates_schema

from ebl.bibliography.application.reference_schema import ReferenceSchema
from ebl.common.application.schemas import deserialize_provenance_record
from ebl.common.domain.manuscript_type import ManuscriptType
from ebl.common.domain.period import Period, PeriodModifier
from ebl.corpus.domain.manuscript import (
    Manuscript,
    OldSiglum,
    is_invalid_non_standard_text,
    is_invalid_standard_text,
)
from ebl.fragmentarium.application.joins_schema import JoinsSchema
from ebl.fragmentarium.domain.joins import Joins
from ebl.provenance.domain.provenance_model import ProvenanceRecord
from ebl.schemas import ValueEnumField
from ebl.transliteration.application.museum_number_schema import MuseumNumberSchema
from ebl.transliteration.application.text_schema import (
    TextSchema as TransliterationSchema,
)
from ebl.transliteration.domain.text import Text as Transliteration


class OldSiglumSchema(Schema):
    __module__ = "ebl.corpus.application.schemas"

    siglum = fields.String(required=True)
    reference = fields.Nested(ReferenceSchema, required=True)

    @post_load
    def make_old_siglum(self, data: dict[str, Any], **kwargs: object) -> OldSiglum:
        return OldSiglum(**data)


class ManuscriptSchema(Schema):
    __module__ = "ebl.corpus.application.schemas"

    id = fields.Integer(required=True)
    siglum_disambiguator = fields.String(required=True, data_key="siglumDisambiguator")
    old_sigla = fields.Nested(
        OldSiglumSchema,
        required=False,
        data_key="oldSigla",
        many=True,
        load_default=(),
    )
    museum_number: fields.Field = fields.Nested(
        MuseumNumberSchema, required=True, allow_none=True, data_key="museumNumber"
    )
    accession = fields.String(required=True)
    period_modifier = ValueEnumField(
        PeriodModifier, required=True, data_key="periodModifier"
    )
    period = fields.Function(
        lambda manuscript: manuscript.period.long_name,
        lambda value: Period.from_name(value),
        required=True,
    )
    provenance = fields.Method(
        "serialize_provenance",
        "deserialize_provenance",
        required=True,
    )
    type = fields.Function(
        lambda manuscript: manuscript.type.long_name,
        lambda value: ManuscriptType.from_name(value),
        required=True,
    )
    notes = fields.String(required=True)
    colophon: fields.Field = fields.Nested(
        TransliterationSchema, load_default=Transliteration()
    )
    unplaced_lines: fields.Field = fields.Nested(
        TransliterationSchema, load_default=Transliteration(), data_key="unplacedLines"
    )
    references = fields.Nested(ReferenceSchema, many=True, required=True)
    joins = fields.Pluck(JoinsSchema, "fragments", load_default=Joins(), load_only=True)
    is_in_fragmentarium = fields.Boolean(
        load_default=False, data_key="isInFragmentarium", load_only=True
    )

    @validates_schema
    def validate_provenance(self, data: dict[str, Any], **kwargs: object) -> None:
        provenace = data["provenance"]
        period = data["period"]
        type_ = data["type"]
        if is_invalid_standard_text(provenace, period, type_):
            raise ValidationError(
                "period and type must be None if provenance is Standard Text"
            )
        elif is_invalid_non_standard_text(provenace, period, type_):
            raise ValidationError(
                "period and type must not be None if provenance is not Standard Text"
            )

    @post_load
    def make_manuscript(self, data: dict[str, Any], **kwargs: object) -> Manuscript:
        return Manuscript(
            data["id"],
            data["siglum_disambiguator"],
            tuple(data["old_sigla"]),
            data["museum_number"],
            data["accession"],
            data["period_modifier"],
            data["period"],
            data["provenance"],
            data["type"],
            data["notes"],
            data["colophon"],
            data["unplaced_lines"],
            tuple(data["references"]),
            data["joins"],
            data["is_in_fragmentarium"],
        )

    def serialize_provenance(self, manuscript: Manuscript) -> str:
        return manuscript.provenance.long_name

    def deserialize_provenance(self, value: str) -> ProvenanceRecord:
        return cast(ProvenanceRecord, deserialize_provenance_record(self, value))
