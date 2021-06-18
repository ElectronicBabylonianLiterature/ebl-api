from marshmallow import fields

from ebl.bibliography.application.reference_schema import ApiReferenceSchema
from ebl.corpus.application.schemas import TextSchema


class ApiTextSchema(TextSchema):
    references = fields.Nested(ApiReferenceSchema, many=True)
