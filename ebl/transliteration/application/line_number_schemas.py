from typing import Mapping, Optional, Type

from marshmallow import Schema, fields, post_load, validate

from ebl.transliteration.domain.line_number import (
    AbstractLineNumber,
    LineNumber,
    LineNumberRange,
)


class LineNumberSchema(Schema):
    type = fields.Constant("LineNumber", required=True)
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
    type = fields.Constant("LineNumberRange", required=True)
    start = fields.Nested(LineNumberSchema, required=True)
    end = fields.Nested(LineNumberSchema, required=True)

    @post_load
    def make_line_number_range(self, data: dict, **kwargs) -> LineNumberRange:
        return LineNumberRange(data["start"], data["end"],)


_SCHEMAS: Mapping[str, Type[Schema]] = {
    "LineNumber": LineNumberSchema,
    "LineNumberRange": LineNumberRangeSchema,
}


def dump_line_number(line_number: Optional[AbstractLineNumber]) -> Optional[dict]:
    return (
        line_number
        if line_number is None
        else _SCHEMAS[type(line_number).__name__]().dump(line_number)
    )


def load_line_number(data: dict) -> AbstractLineNumber:
    return _SCHEMAS[data["type"]]().load(data)
