from marshmallow import Schema, fields

from ebl.corpus.application.schemas import labels
from ebl.corpus.domain.line import ManuscriptLine
from ebl.corpus.domain.manuscript import Manuscript
from ebl.transliteration.application.one_of_line_schema import OneOfLineSchema


def find_manuscript(line: ManuscriptLine, context: dict) -> Manuscript:
    return context["chapter"].get_manuscript(line.manuscript_id)


class ManuscriptLineDisplaySchema(Schema):
    siglum_disambiguator = fields.String(required=True, data_key="siglumDisambiguator")
    period_modifier = fields.Function(
        lambda line, context: find_manuscript(line, context).period_modifier.value,
    )
    period = fields.Function(
        lambda line, context: find_manuscript(line, context).period.long_name,
    )
    provenance = fields.Function(
        lambda line, context: find_manuscript(line, context).provenance.long_name,
    )
    type = fields.Function(
        lambda line, context: find_manuscript(line, context).type.long_name,
    )
    labels = labels()
    line = fields.Nested(OneOfLineSchema, required=True)
    paratext = fields.Nested(OneOfLineSchema, many=True, required=True)


class VariantDisplaySchema(Schema):
    manuscripts = fields.Nested(ManuscriptLineDisplaySchema, many=True, required=True)


class LineDetailsSchema(Schema):
    variants = fields.Nested(VariantDisplaySchema, many=True, required=True)
