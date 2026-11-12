from marshmallow import Schema, fields

from ebl.sumerian_dictionary.domain.sumerian_word_summary import (
    Statistics,
    SumerianWordSummary,
)
from ebl.sumerian_dictionary.infrastructure.sumerian_schema_base import AttrsSchema


class SumerianWordSummarySchema(AttrsSchema):
    model = SumerianWordSummary

    id = fields.String(required=True, data_key="_id")
    citation_form = fields.String(required=True, data_key="citationForm")
    homonym = fields.String(required=True)
    guide_word = fields.String(required=True, data_key="guideWord")
    pos = fields.String(required=True)
    attinger_pos = fields.String(required=True, data_key="attingerPos")
    language = fields.String(required=True)
    cuneiform = fields.String(required=True)
    french_senses = fields.List(fields.String(), required=True, data_key="frenchSenses")
    english_senses = fields.List(
        fields.String(), required=True, data_key="englishSenses"
    )
    has_attinger = fields.Boolean(required=True, data_key="hasAttinger")
    has_epsd2 = fields.Boolean(required=True, data_key="hasEpsd2")
    epsd2_form_count = fields.Integer(required=True, data_key="epsd2FormCount")
    akkadian_count = fields.Integer(required=True, data_key="akkadianCount")
    citation_count = fields.Integer(required=True, data_key="citationCount")
    compound_count = fields.Integer(required=True, data_key="compoundCount")
    cross_reference_count = fields.Integer(
        required=True, data_key="crossReferenceCount"
    )
    has_emesal = fields.Boolean(required=True, data_key="hasEmesal")
    attestation_count = fields.Integer(required=True, data_key="attestationCount")
    matched_alias = fields.String(data_key="matchedAlias", load_default="")


class SearchResultSchema(Schema):
    total = fields.Integer(required=True)
    entries = fields.List(fields.Nested(SumerianWordSummarySchema), required=True)


class StatisticsSchema(AttrsSchema):
    model = Statistics

    lemmas = fields.Integer(required=True)
    attinger = fields.Integer(required=True)
    aligned = fields.Integer(required=True)
    epsd2_only = fields.Integer(required=True, data_key="epsd2Only")
    proper_nouns = fields.Integer(required=True, data_key="properNouns")
    with_akkadian = fields.Integer(required=True, data_key="withAkkadian")
