from marshmallow import Schema, fields, post_load

from ebl.transliteration.domain.line_number import LineNumber


class LineNumberSchema(Schema):
    number = fields.Integer(required=True)
    has_prime = fields.Boolean(required=True, data_key="hasPrime")
    prefix_modifier = fields.String(
        required=True, allow_none=True, data_key="prefixModifier"
    )
    suffix_modifier = fields.String(
        required=True, allow_none=True, data_key="suffixModifier"
    )

    @post_load
    def make_line_number(self, data: dict, **kwargs) -> LineNumber:
        return LineNumber(
            data["number"],
            data["has_prime"],
            data["prefix_modifier"],
            data["suffix_modifier"],
        )
