from abc import abstractmethod
from typing import Mapping, Type

import pydash  # pyre-ignore
from marshmallow import EXCLUDE, Schema, fields, post_dump, post_load  # pyre-ignore
from marshmallow_oneofschema import OneOfSchema  # pyre-ignore

from ebl.schemas import NameEnum, ValueEnum
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.atf import Flag
from ebl.transliteration.domain.enclosure_tokens import (
    AccidentalOmission,
    BrokenAway,
    Determinative,
    DocumentOrientedGloss,
    Erasure,
    Gloss,
    IntentionalOmission,
    LinguisticGloss,
    PerhapsBrokenAway,
    PhoneticGloss,
    Removal,
)
from ebl.transliteration.domain.enclosure_type import EnclosureType
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.side import Side
from ebl.transliteration.domain.sign_tokens import (
    CompoundGrapheme,
    Divider,
    Grapheme,
    Logogram,
    Number,
    Reading,
    UnclearSign,
    UnidentifiedSign,
)
from ebl.transliteration.domain.tokens import (
    Column,
    CommentaryProtocol,
    Joiner,
    LanguageShift,
    Tabulation,
    UnknownNumberOfSigns,
    ValueToken,
    Variant,
    Token
)
from ebl.transliteration.domain.word_tokens import (
    ErasureState,
    InWordNewline,
    LoneDeterminative,
    Word,
)


class BaseTokenSchema(Schema):  # pyre-ignore[11]
    class Meta:
        unknown = EXCLUDE

    enclosure_type = fields.List(
        NameEnum(EnclosureType), missing=list, data_key="enclosureType"
    )

    erasure = NameEnum(ErasureState, missing=ErasureState.NONE)

    clean_value = fields.String(data_key="cleanValue")


class ValueTokenSchema(BaseTokenSchema):
    value = fields.String(required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return ValueToken(
            frozenset(data["enclosure_type"]), data["erasure"], data["value"]
        )


class LanguageShiftSchema(BaseTokenSchema):
    value = fields.String(required=True)
    language = NameEnum(Language, required=True)
    normalized = fields.Boolean(required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return LanguageShift(
            frozenset(data["enclosure_type"]), data["erasure"], data["value"]
        )


class EnclosureSchema(BaseTokenSchema):
    value = fields.String(required=True)
    side = NameEnum(Side, required=True)

    @abstractmethod
    @post_load
    def make_token(self, data, **kwargs) -> Token:
        ...


class DocumentOrientedGlossSchema(EnclosureSchema):
    @post_load
    def make_token(self, data, **kwargs):
        return (
            DocumentOrientedGloss.of(data["side"]).set_enclosure_type(
                frozenset(data["enclosure_type"])
            ).set_erasure(data["erasure"])
        )


class BrokenAwaySchema(EnclosureSchema):
    @post_load
    def make_token(self, data, **kwargs):
        return (
            BrokenAway.of(data["side"]).set_enclosure_type(
                frozenset(data["enclosure_type"])
            ).set_erasure(data["erasure"])
        )


class PerhapsBrokenAwaySchema(EnclosureSchema):
    @post_load
    def make_token(self, data, **kwargs):
        return (
            PerhapsBrokenAway.of(data["side"]).set_enclosure_type(
                frozenset(data["enclosure_type"])
            ).set_erasure(data["erasure"])
        )


class AccidentalOmissionSchema(EnclosureSchema):
    @post_load
    def make_token(self, data, **kwargs):
        return AccidentalOmission.of(data["side"]).set_enclosure_type(
            frozenset(data["enclosure_type"])
        ).set_erasure(data["erasure"])


class IntentionalOmissionSchema(EnclosureSchema):
    @post_load
    def make_token(self, data, **kwargs):
        return IntentionalOmission.of(data["side"]).set_enclosure_type(
            frozenset(data["enclosure_type"])
        ).set_erasure(data["erasure"])


class RemovalSchema(EnclosureSchema):
    @post_load
    def make_token(self, data, **kwargs):
        return Removal.of(data["side"]).set_enclosure_type(
            frozenset(data["enclosure_type"])
        ).set_erasure(data["erasure"])


class ErasureSchema(EnclosureSchema):
    @post_load
    def make_token(self, data, **kwargs):
        return Erasure.of(data["side"]).set_enclosure_type(
            frozenset(data["enclosure_type"])
        ).set_erasure(data["erasure"])


class UnknownNumberOfSignsSchema(BaseTokenSchema):
    value = fields.String(required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return UnknownNumberOfSigns(frozenset(data["enclosure_type"]), data["erasure"])


class TabulationSchema(BaseTokenSchema):
    value = fields.String(required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return Tabulation(frozenset(data["enclosure_type"]), data["erasure"])


class CommentaryProtocolSchema(BaseTokenSchema):
    value = fields.String(required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return CommentaryProtocol(
            frozenset(data["enclosure_type"]), data["erasure"], data["value"]
        )


class DividerSchema(BaseTokenSchema):
    value = fields.String(required=True)
    divider = fields.String(required=True)
    modifiers = fields.List(fields.String(), required=True)
    flags = fields.List(ValueEnum(Flag), required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return Divider.of(
            data["divider"], tuple(data["modifiers"]), tuple(data["flags"]),
        ).set_enclosure_type(
            frozenset(data["enclosure_type"])
        ).set_erasure(data["erasure"])


class ColumnSchema(BaseTokenSchema):
    value = fields.String(required=True)
    number = fields.Integer(missing=None)

    @post_load
    def make_token(self, data, **kwargs):
        return Column.of(data["number"]).set_enclosure_type(
            frozenset(data["enclosure_type"])
        ).set_erasure(data["erasure"])


class UnidentifiedSignSchema(BaseTokenSchema):
    value = fields.String(required=True)
    flags = fields.List(ValueEnum(Flag), required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return UnidentifiedSign.of(tuple(data["flags"])).set_enclosure_type(
            frozenset(data["enclosure_type"])
        ).set_erasure(data["erasure"])


class UnclearSignSchema(BaseTokenSchema):
    value = fields.String(required=True)
    flags = fields.List(ValueEnum(Flag), required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return UnclearSign.of(tuple(data["flags"])).set_enclosure_type(
            frozenset(data["enclosure_type"])
        ).set_erasure(data["erasure"])


class JoinerSchema(BaseTokenSchema):
    value = fields.String()
    enum_value = ValueEnum(atf.Joiner, required=True, data_key="value", load_only=True)

    @post_load
    def make_token(self, data, **kwargs):
        return Joiner(
            frozenset(data["enclosure_type"]), data["erasure"], data["enum_value"]
        )


class InWordNewlineSchema(BaseTokenSchema):
    value = fields.String(required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return InWordNewline(frozenset(data["enclosure_type"]), data["erasure"])


class NamedSignSchema(BaseTokenSchema):
    value = fields.String(required=True)
    name = fields.String(required=True)
    name_parts = fields.List(
        fields.Nested(lambda: OneOfTokenSchema()), required=True, data_key="nameParts"
    )
    sub_index = fields.Integer(data_key="subIndex", allow_none=True)
    modifiers = fields.List(fields.String(), required=True)
    flags = fields.List(ValueEnum(Flag), required=True)
    sign = fields.Nested(lambda: OneOfTokenSchema(), allow_none=True)


class ReadingSchema(NamedSignSchema):
    @post_load
    def make_token(self, data, **kwargs):
        return Reading.of(
            data["name_parts"],
            data["sub_index"],
            data["modifiers"],
            data["flags"],
            data["sign"],
        ).set_enclosure_type(
            frozenset(data["enclosure_type"])
        ).set_erasure(data["erasure"])


class LogogramSchema(NamedSignSchema):
    surrogate = fields.List(fields.Nested(lambda: OneOfTokenSchema()), missing=tuple())

    @post_load
    def make_token(self, data, **kwargs):
        return Logogram.of(
            data["name_parts"],
            data["sub_index"],
            data["modifiers"],
            data["flags"],
            data["sign"],
            data["surrogate"],
        ).set_enclosure_type(
            frozenset(data["enclosure_type"])
        ).set_erasure(data["erasure"])


class NumberSchema(NamedSignSchema):
    @post_load
    def make_token(self, data, **kwargs):
        return Number.of(
            data["name_parts"],
            data["modifiers"],
            data["flags"],
            data["sign"],
            data["sub_index"],
        ).set_enclosure_type(
            frozenset(data["enclosure_type"])
        ).set_erasure(data["erasure"])


class WordSchema(BaseTokenSchema):
    value = fields.String(required=True)
    language = NameEnum(Language, required=True)
    normalized = fields.Boolean(required=True)
    lemmatizable = fields.Boolean(required=True)
    unique_lemma = fields.List(fields.String(), data_key="uniqueLemma", required=True)
    alignment = fields.Integer(allow_none=True, missing=None)
    parts = fields.List(fields.Nested(lambda: OneOfTokenSchema()), missing=tuple())

    @post_load
    def make_token(self, data, **kwargs):
        return Word.of(
            data["parts"],
            data["language"],
            data["normalized"],
            tuple(data["unique_lemma"]),
            data["erasure"],
            data["alignment"],
        ).set_enclosure_type(frozenset(data["enclosure_type"]))

    @post_dump
    def dump_token(self, data, **kwargs):
        return pydash.omit_by(data, lambda value: value is None,)


class LoneDeterminativeSchema(BaseTokenSchema):
    value = fields.String(required=True)
    language = NameEnum(Language, required=True)
    normalized = fields.Boolean(required=True)
    lemmatizable = fields.Boolean(required=True)
    unique_lemma = fields.List(fields.String(), data_key="uniqueLemma", required=True)
    erasure = NameEnum(ErasureState, missing=ErasureState.NONE)
    alignment = fields.Integer(allow_none=True, missing=None)
    parts = fields.List(fields.Nested(lambda: OneOfTokenSchema()), missing=tuple())

    @post_load
    def make_token(self, data, **kwargs):
        return LoneDeterminative.of(
            data["parts"],
            data["language"],
            data["normalized"],
            tuple(data["unique_lemma"]),
            data["erasure"],
            data["alignment"],
        ).set_enclosure_type(frozenset(data["enclosure_type"]))

    @post_dump
    def dump_token(self, data, **kwargs):
        return pydash.omit_by(data, lambda value: value is None,)


class VariantSchema(BaseTokenSchema):
    value = fields.String()
    tokens = fields.List(fields.Nested(lambda: OneOfTokenSchema()), required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return Variant.of(*data["tokens"]).set_enclosure_type(
            frozenset(data["enclosure_type"])
        ).set_erasure(data["erasure"])


class GraphemeSchema(BaseTokenSchema):
    value = fields.String(required=True)
    name = fields.String(required=True)
    modifiers = fields.List(fields.String(), required=True)
    flags = fields.List(ValueEnum(Flag), required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return Grapheme.of(
            data["name"], data["modifiers"], data["flags"]
        ).set_enclosure_type(
            frozenset(data["enclosure_type"])
        ).set_erasure(data["erasure"])


class CompoundGraphemeSchema(BaseTokenSchema):
    value = fields.String(required=True)
    compound_parts = fields.List(fields.String())

    @post_load
    def make_token(self, data, **kwargs):
        grapheme = (CompoundGrapheme.of(data["compound_parts"])
                    if "compound_parts" in data
                    else CompoundGrapheme.of([data["value"].strip('|')]))
        return grapheme.set_enclosure_type(
            frozenset(data["enclosure_type"])
        ).set_erasure(data["erasure"])


class GlossSchema(BaseTokenSchema):
    value = fields.String()
    parts = fields.List(fields.Nested(lambda: OneOfTokenSchema()), required=True)

    @abstractmethod
    @post_load
    def make_token(self, data, **kwargs) -> Gloss:
        ...


class DeterminativeSchema(GlossSchema):
    @post_load
    def make_token(self, data, **kwargs):
        return Determinative.of(data["parts"]).set_enclosure_type(
            frozenset(data["enclosure_type"])
        ).set_erasure(data["erasure"])


class PhoneticGlossSchema(GlossSchema):
    @post_load
    def make_token(self, data, **kwargs):
        return PhoneticGloss.of(data["parts"]).set_enclosure_type(
            frozenset(data["enclosure_type"])
        ).set_erasure(data["erasure"])


class LinguisticGlossSchema(GlossSchema):
    @post_load
    def make_token(self, data, **kwargs):
        return LinguisticGloss.of(data["parts"]).set_enclosure_type(
            frozenset(data["enclosure_type"])
        ).set_erasure(data["erasure"])


class OneOfTokenSchema(OneOfSchema):  # pyre-ignore[11]
    type_field = "type"
    type_schemas: Mapping[str, Type[BaseTokenSchema]] = {
        "Token": ValueTokenSchema,
        "ValueToken": ValueTokenSchema,
        "Word": WordSchema,
        "LanguageShift": LanguageShiftSchema,
        "LoneDeterminative": LoneDeterminativeSchema,
        "DocumentOrientedGloss": DocumentOrientedGlossSchema,
        "BrokenAway": BrokenAwaySchema,
        "PerhapsBrokenAway": PerhapsBrokenAwaySchema,
        "AccidentalOmission": AccidentalOmissionSchema,
        "IntentionalOmission": IntentionalOmissionSchema,
        "Removal": RemovalSchema,
        "Erasure": ErasureSchema,
        "UnknownNumberOfSigns": UnknownNumberOfSignsSchema,
        "Tabulation": TabulationSchema,
        "CommentaryProtocol": CommentaryProtocolSchema,
        "Divider": DividerSchema,
        "Column": ColumnSchema,
        "Variant": VariantSchema,
        "UnidentifiedSign": UnidentifiedSignSchema,
        "UnclearSign": UnclearSignSchema,
        "Joiner": JoinerSchema,
        "InWordNewline": InWordNewlineSchema,
        "Reading": ReadingSchema,
        "Logogram": LogogramSchema,
        "Number": NumberSchema,
        "CompoundGrapheme": CompoundGraphemeSchema,
        "Grapheme": GraphemeSchema,
        "Determinative": DeterminativeSchema,
        "PhoneticGloss": PhoneticGlossSchema,
        "LinguisticGloss": LinguisticGlossSchema,
    }
