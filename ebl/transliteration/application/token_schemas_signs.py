from abc import abstractmethod

from marshmallow import fields, post_load

from ebl.schemas import ValueEnumField
from ebl.transliteration.application.token_schemas_enclosures import BaseTokenSchema
from ebl.transliteration.domain.atf import Flag
from ebl.transliteration.domain.enclosure_tokens import (
    Determinative,
    Gloss,
    LinguisticGloss,
    PhoneticGloss,
)
from ebl.transliteration.domain.sign_tokens import (
    CompoundGrapheme,
    Grapheme,
    Logogram,
    Number,
    Reading,
)
from ebl.transliteration.domain.tokens import (
    LineBreak,
    Variant,
)


class NamedSignSchema(BaseTokenSchema):
    name = fields.String(required=True)
    name_parts = fields.List(
        fields.Nested("OneOfTokenSchema"), required=True, data_key="nameParts"
    )
    sub_index = fields.Integer(data_key="subIndex", allow_none=True)
    modifiers = fields.List(fields.String(), required=True)
    flags = fields.List(ValueEnumField(Flag), required=True)
    sign = fields.Nested("OneOfTokenSchema", allow_none=True)


class ReadingSchema(NamedSignSchema):
    @post_load
    def make_token(self, data, **kwargs):
        return (
            Reading.of(
                data["name_parts"],
                data["sub_index"],
                data["modifiers"],
                data["flags"],
                data["sign"],
            )
            .set_enclosure_type(frozenset(data["enclosure_type"]))
            .set_erasure(data["erasure"])
        )


class LogogramSchema(NamedSignSchema):
    surrogate = fields.List(fields.Nested("OneOfTokenSchema"), load_default=())

    @post_load
    def make_token(self, data, **kwargs):
        return (
            Logogram.of(
                data["name_parts"],
                data["sub_index"],
                data["modifiers"],
                data["flags"],
                data["sign"],
                data["surrogate"],
            )
            .set_enclosure_type(frozenset(data["enclosure_type"]))
            .set_erasure(data["erasure"])
        )


class NumberSchema(NamedSignSchema):
    @post_load
    def make_token(self, data, **kwargs):
        return (
            Number.of(
                data["name_parts"],
                data["modifiers"],
                data["flags"],
                data["sign"],
                data["sub_index"],
            )
            .set_enclosure_type(frozenset(data["enclosure_type"]))
            .set_erasure(data["erasure"])
        )


class VariantSchema(BaseTokenSchema):
    tokens = fields.List(fields.Nested("OneOfTokenSchema"), required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return (
            Variant.of(*data["tokens"])
            .set_enclosure_type(frozenset(data["enclosure_type"]))
            .set_erasure(data["erasure"])
        )


class GraphemeSchema(BaseTokenSchema):
    name = fields.String(required=True)
    modifiers = fields.List(fields.String(), required=True)
    flags = fields.List(ValueEnumField(Flag), required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return (
            Grapheme.of(data["name"], data["modifiers"], data["flags"])
            .set_enclosure_type(frozenset(data["enclosure_type"]))
            .set_erasure(data["erasure"])
        )


class CompoundGraphemeSchema(BaseTokenSchema):
    compound_parts = fields.List(fields.String())

    @post_load
    def make_token(self, data, **kwargs):
        return (
            CompoundGrapheme.of(data["compound_parts"])
            .set_enclosure_type(frozenset(data["enclosure_type"]))
            .set_erasure(data["erasure"])
        )


class GlossSchema(BaseTokenSchema):
    parts = fields.List(fields.Nested("OneOfTokenSchema"), required=True)

    @abstractmethod
    @post_load
    def make_token(self, data, **kwargs) -> Gloss:
        raise NotImplementedError


class DeterminativeSchema(GlossSchema):
    @post_load
    def make_token(self, data, **kwargs):
        return (
            Determinative.of(data["parts"])
            .set_enclosure_type(frozenset(data["enclosure_type"]))
            .set_erasure(data["erasure"])
        )


class PhoneticGlossSchema(GlossSchema):
    @post_load
    def make_token(self, data, **kwargs):
        return (
            PhoneticGloss.of(data["parts"])
            .set_enclosure_type(frozenset(data["enclosure_type"]))
            .set_erasure(data["erasure"])
        )


class LinguisticGlossSchema(GlossSchema):
    @post_load
    def make_token(self, data, **kwargs):
        return (
            LinguisticGloss.of(data["parts"])
            .set_enclosure_type(frozenset(data["enclosure_type"]))
            .set_erasure(data["erasure"])
        )


class LineBreakSchema(BaseTokenSchema):
    @post_load
    def make_token(self, data, **kwargs):
        return LineBreak(frozenset(data["enclosure_type"]), data["erasure"])
