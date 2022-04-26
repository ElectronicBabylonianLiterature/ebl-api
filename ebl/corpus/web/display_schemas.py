from marshmallow import Schema, fields
from ebl.transliteration.application.one_of_line_schema import OneOfLineSchema
from ebl.corpus.application.schemas import labels
from ebl.corpus.web.chapter_schemas import ApiOldSiglumSchema
from ebl.bibliography.application.reference_schema import ApiReferenceSchema
from operator import attrgetter


def get_manuscript_field(field_name):
    return lambda line, context: attrgetter(field_name)(
        context["manuscripts"][line.manuscript_id]
    )


class ManuscriptLineDisplaySchema(Schema):
    old_sigla = fields.Function(
        lambda line, context: ApiOldSiglumSchema().dump(
            get_manuscript_field("old_sigla")(line, context), many=True
        ),
        data_key="oldSigla",
    )
    references = fields.Function(
        lambda line, context: ApiReferenceSchema().dump(
            get_manuscript_field("references")(line, context), many=True
        ),
    )
    siglum_disambiguator = fields.Function(
        get_manuscript_field("siglum_disambiguator"),
        data_key="siglumDisambiguator",
    )
    period_modifier = fields.Function(
        get_manuscript_field("period_modifier.value"),
        data_key="periodModifier",
    )
    period = fields.Function(
        get_manuscript_field("period.long_name"),
    )
    provenance = fields.Function(
        get_manuscript_field("provenance.long_name"),
    )
    type = fields.Function(
        get_manuscript_field("type.long_name"),
    )
    labels = labels()
    line = fields.Nested(OneOfLineSchema, required=True)
    paratext = fields.Nested(OneOfLineSchema, many=True, required=True)


class VariantDisplaySchema(Schema):
    manuscripts = fields.Nested(ManuscriptLineDisplaySchema, many=True, required=True)


class LineDetailsSchema(Schema):
    variants = fields.Nested(VariantDisplaySchema, many=True, required=True)
