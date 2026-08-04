from marshmallow import fields, post_load

from ebl.schemas import ValueEnumField
from ebl.transliteration.application.token_schemas_enclosures import BaseTokenSchema
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.atf import Flag
from ebl.transliteration.domain.egyptian_metrical_feet_separator_token import (
    EgyptianMetricalFeetSeparator,
)
from ebl.transliteration.domain.sign_tokens import Divider
from ebl.transliteration.domain.tokens import (
    Column,
    CommentaryProtocol,
    Joiner,
    WordOmitted,
    Tabulation,
    UnknownNumberOfSigns,
)
from ebl.transliteration.domain.unknown_sign_tokens import UnclearSign, UnidentifiedSign
from ebl.transliteration.domain.word_tokens import InWordNewline


class UnknownNumberOfSignsSchema(BaseTokenSchema):
    @post_load
    def make_token(self, data, **kwargs):
        return UnknownNumberOfSigns(frozenset(data["enclosure_type"]), data["erasure"])


class EgyptianMetricalFeetSeparatorSchema(BaseTokenSchema):
    flags = fields.List(ValueEnumField(Flag), required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return (
            EgyptianMetricalFeetSeparator.of(tuple(data["flags"]))
            .set_enclosure_type(frozenset(data["enclosure_type"]))
            .set_erasure(data["erasure"])
        )


class WordOmittedSchema(BaseTokenSchema):
    @post_load
    def make_token(self, data, **kwargs):
        return WordOmitted(frozenset(data["enclosure_type"]), data["erasure"])


class TabulationSchema(BaseTokenSchema):
    @post_load
    def make_token(self, data, **kwargs):
        return Tabulation(frozenset(data["enclosure_type"]), data["erasure"])


class CommentaryProtocolSchema(BaseTokenSchema):
    @post_load
    def make_token(self, data, **kwargs):
        return CommentaryProtocol(
            frozenset(data["enclosure_type"]), data["erasure"], data["value"]
        )


class DividerSchema(BaseTokenSchema):
    divider = fields.String(required=True)
    modifiers = fields.List(fields.String(), required=True)
    flags = fields.List(ValueEnumField(Flag), required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return (
            Divider.of(data["divider"], tuple(data["modifiers"]), tuple(data["flags"]))
            .set_enclosure_type(frozenset(data["enclosure_type"]))
            .set_erasure(data["erasure"])
        )


class ColumnSchema(BaseTokenSchema):
    number = fields.Integer(load_default=None)

    @post_load
    def make_token(self, data, **kwargs):
        return (
            Column.of(data["number"])
            .set_enclosure_type(frozenset(data["enclosure_type"]))
            .set_erasure(data["erasure"])
        )


class UnidentifiedSignSchema(BaseTokenSchema):
    flags = fields.List(ValueEnumField(Flag), required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return (
            UnidentifiedSign.of(tuple(data["flags"]))
            .set_enclosure_type(frozenset(data["enclosure_type"]))
            .set_erasure(data["erasure"])
        )


class UnclearSignSchema(BaseTokenSchema):
    flags = fields.List(ValueEnumField(Flag), required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return (
            UnclearSign.of(tuple(data["flags"]))
            .set_enclosure_type(frozenset(data["enclosure_type"]))
            .set_erasure(data["erasure"])
        )


class JoinerSchema(BaseTokenSchema):
    enum_value = ValueEnumField(
        atf.Joiner, required=True, data_key="value", load_only=True
    )

    @post_load
    def make_token(self, data, **kwargs):
        return Joiner(
            frozenset(data["enclosure_type"]), data["erasure"], data["enum_value"]
        )


class InWordNewlineSchema(BaseTokenSchema):
    @post_load
    def make_token(self, data, **kwargs):
        return InWordNewline(frozenset(data["enclosure_type"]), data["erasure"])
