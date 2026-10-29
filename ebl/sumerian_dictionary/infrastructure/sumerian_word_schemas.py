from marshmallow import fields, validate

from ebl.sumerian_dictionary.domain.sumerian_word import SumerianWord
from ebl.sumerian_dictionary.infrastructure.sumerian_schema_base import (
    LANGUAGES,
    AttrsSchema,
)
from ebl.sumerian_dictionary.infrastructure.sumerian_word_link_schemas import (
    AliasSchema,
    CrossReferenceSchema,
    HeadIdField,
    WordLinkSchema,
)
from ebl.sumerian_dictionary.infrastructure.sumerian_word_part_schemas import (
    AkkadianEquivalentSchema,
    AttestationSchema,
    AttingerFormSchema,
    AttingerSenseSchema,
    CitationSchema,
    EmesalFormSchema,
    Epsd2FormSchema,
    Epsd2SenseSchema,
    RenderingSchema,
    SignEntrySchema,
)
from ebl.sumerian_dictionary.infrastructure.sumerian_word_source_schemas import (
    MatchSchema,
    SourcesSchema,
)


def _strings(data_key: str = "") -> fields.List:
    return fields.List(fields.String(), required=True, data_key=data_key or None)


def _nested(schema: type, data_key: str = "") -> fields.List:
    return fields.List(fields.Nested(schema), required=True, data_key=data_key or None)


class SumerianWordBaseSchema(AttrsSchema):
    model = SumerianWord

    id = fields.String(required=True, data_key="_id")
    citation_form = fields.String(required=True, data_key="citationForm")
    lemma = _strings()
    homonym = fields.String(required=True)
    guide_word = fields.String(required=True, data_key="guideWord")
    pos = fields.String(required=True)
    attinger_pos = fields.String(required=True, data_key="attingerPos")
    language = fields.String(required=True, validate=validate.OneOf(LANGUAGES))
    uncertain = fields.Boolean(required=True)
    stems = _strings()
    determinatives = _strings()
    case_frame = _strings("caseFrame")
    emesal = _nested(EmesalFormSchema)
    attinger_senses = _nested(AttingerSenseSchema, "attingerSenses")
    epsd2_senses = _nested(Epsd2SenseSchema, "epsd2Senses")
    attinger_forms = _nested(AttingerFormSchema, "attingerForms")
    epsd2_forms = _nested(Epsd2FormSchema, "epsd2Forms")
    signs = _nested(SignEntrySchema)
    renderings = _nested(RenderingSchema)
    compounds = _nested(WordLinkSchema)
    name_compounds = _nested(WordLinkSchema, "nameCompounds")
    cross_references = _nested(CrossReferenceSchema, "crossReferences")
    aliases = _nested(AliasSchema)
    akkadian_equivalents = _nested(AkkadianEquivalentSchema, "akkadianEquivalents")
    citations = _nested(CitationSchema)
    attestation = fields.Nested(AttestationSchema, required=True)
    sources = fields.Nested(SourcesSchema, required=True)
    match = fields.Nested(MatchSchema, required=True)
    atf = fields.String(load_default="")
    truncated = fields.Boolean(load_default=False)


class SumerianWordSchema(SumerianWordBaseSchema):
    head = fields.Nested(WordLinkSchema, allow_none=True, load_default=None)


class SumerianWordDocumentSchema(SumerianWordBaseSchema):
    head = HeadIdField(allow_none=True, load_default=None)
