from typing import Mapping, Type

from marshmallow import EXCLUDE, Schema, fields, post_load, validate
from marshmallow_oneofschema import OneOfSchema

from ebl.bibliography.application.reference_schema import ApiReferenceSchema
from ebl.transliteration.domain.line_number import (
    LineNumber,
    LineNumberRange,
    OldLineNumber,
)


class OldLineNumberSchema(Schema):
    number = fields.String(required=True)
    reference = fields.Nested(ApiReferenceSchema, required=True)

    @post_load
    def make_old_line_number(self, data: dict, **kwargs) -> OldLineNumber:
        return OldLineNumber(data["number"], data["reference"])


class LineNumberSchema(Schema):
    number = fields.Integer(required=True, validate=validate.Range(min=0))
    has_prime = fields.Boolean(required=True, data_key="hasPrime")
    prefix_modifier = fields.String(
        required=True,
        allow_none=True,
        validate=validate.Length(min=1, max=1),
        data_key="prefixModifier",
    )
    suffix_modifier = fields.String(
        required=True,
        allow_none=True,
        validate=validate.Length(min=1, max=1),
        data_key="suffixModifier",
    )

    @post_load
    def make_line_number(self, data: dict, **kwargs) -> LineNumber:
        return LineNumber(
            data["number"],
            data["has_prime"],
            data["prefix_modifier"],
            data["suffix_modifier"],
        )


class LineNumberRangeSchema(Schema):
    start = fields.Nested(LineNumberSchema, required=True, unknown=EXCLUDE)
    end = fields.Nested(LineNumberSchema, required=True, unknown=EXCLUDE)

    @post_load
    def make_line_number_range(self, data: dict, **kwargs) -> LineNumberRange:
        return LineNumberRange(data["start"], data["end"])


class OneOfLineNumberSchema(OneOfSchema):
    type_field = "type"
    type_schemas: Mapping[str, Type[Schema]] = {
        "LineNumber": LineNumberSchema,
        "LineNumberRange": LineNumberRangeSchema,
    }
