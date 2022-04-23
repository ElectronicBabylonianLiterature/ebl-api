from marshmallow import Schema, fields
from ebl.transliteration.application.one_of_line_schema import OneOfLineSchema
from ebl.corpus.application.schemas import (
    labels,
    OldSiglumSchema,
)

def get_old_sigla(line, context):
    m = context["manuscripts"][line.manuscript_id]
    sigs = m.old_sigla

    return OldSiglumSchema().dump(sigs, many=True)

class ManuscriptLineDisplaySchema(Schema):
    old_sigla = fields.Function(
        lambda line, context: OldSiglumSchema().dump(
            context["manuscripts"][line.manuscript_id].old_sigla, many=True
        ),
        data_key="oldSigla",
    )
    siglum_disambiguator = fields.Function(
        lambda line, context: context["manuscripts"][
            line.manuscript_id
        ].siglum_disambiguator,
        data_key="siglumDisambiguator",
    )
    period_modifier = fields.Function(
        lambda line, context: context["manuscripts"][
            line.manuscript_id
        ].period_modifier.value,
        data_key="periodModifier",
    )
    period = fields.Function(
        lambda line, context: context["manuscripts"][
            line.manuscript_id
        ].period.long_name,
    )
    provenance = fields.Function(
        lambda line, context: context["manuscripts"][
            line.manuscript_id
        ].provenance.long_name,
    )
    type = fields.Function(
        lambda line, context: context["manuscripts"][line.manuscript_id].type.long_name,
    )
    labels = labels()
    line = fields.Nested(OneOfLineSchema, required=True)
    paratext = fields.Nested(OneOfLineSchema, many=True, required=True)


class VariantDisplaySchema(Schema):
    manuscripts = fields.Nested(ManuscriptLineDisplaySchema, many=True, required=True)


class LineDetailsSchema(Schema):
    variants = fields.Nested(VariantDisplaySchema, many=True, required=True)
