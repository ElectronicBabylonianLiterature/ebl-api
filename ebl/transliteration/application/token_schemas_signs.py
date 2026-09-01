from abc import abstractmethod
from typing import Any, Dict, Sequence

from marshmallow import fields, post_load, pre_load, validate

from ebl.schemas import ValueEnumField
from ebl.transliteration.application.token_schemas_enclosures import (
    BaseTokenSchema,
    BrokenAwaySchema,
    ValueTokenSchema,
)
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
from ebl.transliteration.domain.sign_token_base import NamedSignArguments
from ebl.transliteration.domain.tokens import (
    LineBreak,
    Variant,
)


class NameValueTokenSchema(ValueTokenSchema):
    type = fields.String(
        validate=validate.Equal("ValueToken"),
        load_default="ValueToken",
        dump_default="ValueToken",
    )


class NameBreakSchema(BrokenAwaySchema):
    type = fields.String(
        validate=validate.Equal("BrokenAway"),
        load_default="BrokenAway",
        dump_default="BrokenAway",
    )


def named_sign_arguments(data: Dict[str, Any]) -> NamedSignArguments:
    return NamedSignArguments(
        data["name_parts"],
        data["sub_index"],
        data["modifiers"],
        data["flags"],
        data["name_breaks"],
    )


class NamedSignSchema(BaseTokenSchema):
    name = fields.String(required=True)
    name_parts = fields.List(
        fields.Nested(NameValueTokenSchema), required=True, data_key="nameParts"
    )
    name_breaks = fields.List(
        fields.Nested(NameBreakSchema), load_default=(), data_key="nameBreaks"
    )
    sub_index = fields.Integer(data_key="subIndex", allow_none=True)
    modifiers = fields.List(fields.String(), required=True)
    flags = fields.List(ValueEnumField(Flag), required=True)
    sign = fields.Nested("OneOfTokenSchema", allow_none=True)

    @pre_load
    def separate_legacy_name_parts(
        self, data: Dict[str, Any], **kwargs
    ) -> Dict[str, Any]:
        if not isinstance(data, dict) or "nameBreaks" in data:
            return data
        legacy_parts = data.get("nameParts")
        if not isinstance(legacy_parts, Sequence) or isinstance(legacy_parts, str):
            return data
        return {
            **data,
            "nameParts": list(legacy_parts[0::2]),
            "nameBreaks": list(legacy_parts[1::2]),
        }


class ReadingSchema(NamedSignSchema):
    @post_load
    def make_token(self, data: Dict[str, Any], **kwargs) -> Reading:
        return (
            Reading.of_arguments(named_sign_arguments(data))
            .with_sign(data["sign"])
            .set_enclosure_type(frozenset(data["enclosure_type"]))
            .set_erasure(data["erasure"])
        )


class LogogramSchema(NamedSignSchema):
    surrogate = fields.List(fields.Nested("OneOfTokenSchema"), load_default=())

    @post_load
    def make_token(self, data: Dict[str, Any], **kwargs) -> Logogram:
        return (
            Logogram.of_arguments(named_sign_arguments(data))
            .with_sign(data["sign"])
            .with_surrogate(data["surrogate"])
            .set_enclosure_type(frozenset(data["enclosure_type"]))
            .set_erasure(data["erasure"])
        )


class NumberSchema(NamedSignSchema):
    @post_load
    def make_token(self, data: Dict[str, Any], **kwargs) -> Number:
        return (
            Number.of_arguments(named_sign_arguments(data))
            .with_sign(data["sign"])
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
