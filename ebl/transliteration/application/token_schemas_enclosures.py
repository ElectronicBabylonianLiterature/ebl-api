from abc import abstractmethod

from marshmallow import EXCLUDE, Schema, fields, post_load

from ebl.schemas import NameEnumField
from ebl.transliteration.domain.enclosure_tokens import (
    AccidentalOmission,
    BrokenAway,
    DocumentOrientedGloss,
    Emendation,
    Erasure,
    IntentionalOmission,
    PerhapsBrokenAway,
    Removal,
)
from ebl.transliteration.domain.enclosure_type import EnclosureType
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.side import Side
from ebl.transliteration.domain.tokens import (
    LanguageShift,
    Token,
    ValueToken,
)
from ebl.transliteration.domain.word_tokens import ErasureState


class BaseTokenSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    value = fields.String(required=True)
    clean_value = fields.String(data_key="cleanValue")
    enclosure_type = fields.List(
        NameEnumField(EnclosureType), load_default=list, data_key="enclosureType"
    )
    erasure = NameEnumField(ErasureState, load_default=ErasureState.NONE)


class ValueTokenSchema(BaseTokenSchema):
    @post_load
    def make_token(self, data, **kwargs):
        return ValueToken(
            frozenset(data["enclosure_type"]), data["erasure"], data["value"]
        )


class LanguageShiftSchema(BaseTokenSchema):
    language = NameEnumField(Language, required=True)
    normalized = fields.Boolean(required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return LanguageShift(
            frozenset(data["enclosure_type"]), data["erasure"], data["value"]
        )


class EnclosureSchema(BaseTokenSchema):
    side = NameEnumField(Side, required=True)

    @abstractmethod
    @post_load
    def make_token(self, data, **kwargs) -> Token:
        raise NotImplementedError


class DocumentOrientedGlossSchema(EnclosureSchema):
    @post_load
    def make_token(self, data, **kwargs):
        return (
            DocumentOrientedGloss.of(data["side"])
            .set_enclosure_type(frozenset(data["enclosure_type"]))
            .set_erasure(data["erasure"])
        )


class BrokenAwaySchema(EnclosureSchema):
    @post_load
    def make_token(self, data, **kwargs):
        return (
            BrokenAway.of(data["side"])
            .set_enclosure_type(frozenset(data["enclosure_type"]))
            .set_erasure(data["erasure"])
        )


class PerhapsBrokenAwaySchema(EnclosureSchema):
    @post_load
    def make_token(self, data, **kwargs):
        return (
            PerhapsBrokenAway.of(data["side"])
            .set_enclosure_type(frozenset(data["enclosure_type"]))
            .set_erasure(data["erasure"])
        )


class AccidentalOmissionSchema(EnclosureSchema):
    @post_load
    def make_token(self, data, **kwargs):
        return (
            AccidentalOmission.of(data["side"])
            .set_enclosure_type(frozenset(data["enclosure_type"]))
            .set_erasure(data["erasure"])
        )


class IntentionalOmissionSchema(EnclosureSchema):
    @post_load
    def make_token(self, data, **kwargs):
        return (
            IntentionalOmission.of(data["side"])
            .set_enclosure_type(frozenset(data["enclosure_type"]))
            .set_erasure(data["erasure"])
        )


class RemovalSchema(EnclosureSchema):
    @post_load
    def make_token(self, data, **kwargs):
        return (
            Removal.of(data["side"])
            .set_enclosure_type(frozenset(data["enclosure_type"]))
            .set_erasure(data["erasure"])
        )


class EmendationSchema(EnclosureSchema):
    @post_load
    def make_token(self, data, **kwargs):
        return (
            Emendation.of(data["side"])
            .set_enclosure_type(frozenset(data["enclosure_type"]))
            .set_erasure(data["erasure"])
        )


class ErasureSchema(EnclosureSchema):
    @post_load
    def make_token(self, data, **kwargs):
        return (
            Erasure.of(data["side"])
            .set_enclosure_type(frozenset(data["enclosure_type"]))
            .set_erasure(data["erasure"])
        )
