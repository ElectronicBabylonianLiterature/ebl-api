from abc import abstractmethod
from typing import Mapping, Type

import pydash
from marshmallow import EXCLUDE, Schema, fields, post_dump, post_load, validate
from marshmallow_oneofschema import OneOfSchema

from ebl.schemas import NameEnumField, ValueEnumField
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.atf import Flag
from ebl.transliteration.domain.egyptian_metrical_feet_separator_token import (
    EgyptianMetricalFeetSeparator,
)
from ebl.transliteration.domain.enclosure_tokens import (
    AccidentalOmission,
    BrokenAway,
    Determinative,
    DocumentOrientedGloss,
    Emendation,
    Erasure,
    Gloss,
    IntentionalOmission,
    LinguisticGloss,
    PerhapsBrokenAway,
    PhoneticGloss,
    Removal,
)
from ebl.transliteration.domain.enclosure_type import EnclosureType
from ebl.transliteration.domain.greek_tokens import GreekLetter, GreekWord
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.normalized_akkadian import (
    AkkadianWord,
    Caesura,
    MetricalFootSeparator,
)
from ebl.transliteration.domain.side import Side
from ebl.transliteration.domain.sign_tokens import (
    CompoundGrapheme,
    Divider,
    Grapheme,
    Logogram,
    Number,
    Reading,
)
from ebl.transliteration.domain.tokens import (
    Column,
    CommentaryProtocol,
    Joiner,
    LanguageShift,
    LineBreak,
    Tabulation,
    Token,
    UnknownNumberOfSigns,
    ValueToken,
    Variant,
)
from ebl.transliteration.domain.unknown_sign_tokens import UnclearSign, UnidentifiedSign
from ebl.transliteration.domain.word_tokens import (
    ErasureState,
    InWordNewline,
    LoneDeterminative,
    Word,
)


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
        ...


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


class NamedSignSchema(BaseTokenSchema):
    name = fields.String(required=True)
    name_parts = fields.List(
        fields.Nested(lambda: OneOfTokenSchema()), required=True, data_key="nameParts"
    )
    sub_index = fields.Integer(data_key="subIndex", allow_none=True)
    modifiers = fields.List(fields.String(), required=True)
    flags = fields.List(ValueEnumField(Flag), required=True)
    sign = fields.Nested(lambda: OneOfTokenSchema(), allow_none=True)


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
    surrogate = fields.List(
        fields.Nested(lambda: OneOfTokenSchema()), load_default=tuple()
    )

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


class BaseWordSchema(BaseTokenSchema):
    parts = fields.List(fields.Nested(lambda: OneOfTokenSchema()), required=True)
    language = NameEnumField(Language, required=True)
    normalized = fields.Boolean(required=True)
    lemmatizable = fields.Boolean(required=True)
    alignable = fields.Boolean()
    unique_lemma = fields.List(fields.String(), data_key="uniqueLemma", required=True)
    alignment = fields.Integer(allow_none=True, load_default=None)
    variant = fields.Nested(
        lambda: OneOfWordSchema(), allow_none=True, load_default=None
    )
    has_variant_alignment = fields.Boolean(
        load_default=False, data_key="hasVariantAlignment"
    )
    has_omitted_alignment = fields.Boolean(
        load_default=False, data_key="hasOmittedAlignment"
    )


class WordSchema(BaseWordSchema):
    @post_load
    def make_token(self, data, **kwargs):
        return Word.of(
            data["parts"],
            data["language"],
            tuple(data["unique_lemma"]),
            data["erasure"],
            data["alignment"],
            data["variant"],
            data["has_variant_alignment"],
            data["has_omitted_alignment"],
        ).set_enclosure_type(frozenset(data["enclosure_type"]))

    @post_dump
    def dump_token(self, data, **kwargs):
        return pydash.omit_by(data, lambda value: value is None)


class LoneDeterminativeSchema(BaseWordSchema):
    @post_load
    def make_token(self, data, **kwargs):
        return LoneDeterminative.of(
            data["parts"],
            data["language"],
            tuple(data["unique_lemma"]),
            data["erasure"],
            data["alignment"],
            data["variant"],
            data["has_variant_alignment"],
            data["has_omitted_alignment"],
        ).set_enclosure_type(frozenset(data["enclosure_type"]))

    @post_dump
    def dump_token(self, data, **kwargs):
        return pydash.omit_by(data, lambda value: value is None)


class VariantSchema(BaseTokenSchema):
    tokens = fields.List(fields.Nested(lambda: OneOfTokenSchema()), required=True)

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
    parts = fields.List(fields.Nested(lambda: OneOfTokenSchema()), required=True)

    @abstractmethod
    @post_load
    def make_token(self, data, **kwargs) -> Gloss:
        ...


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


class AkkadianWordSchema(BaseWordSchema):
    modifiers = fields.List(ValueEnumField(Flag), required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return AkkadianWord.of(
            tuple(data["parts"]),
            tuple(data["modifiers"]),
            tuple(data["unique_lemma"]),
            data["alignment"],
            data["variant"],
            data["has_variant_alignment"],
            data["has_omitted_alignment"],
        ).set_enclosure_type(frozenset(data["enclosure_type"]))


class BreakSchema(BaseTokenSchema):
    is_uncertain = fields.Boolean(data_key="isUncertain", required=True)


class CaesuraSchema(BreakSchema):
    @post_load
    def make_token(self, data, **kwargs):
        return Caesura.of(data["is_uncertain"]).set_enclosure_type(
            frozenset(data["enclosure_type"])
        )


class MetricalFootSeparatorSchema(BreakSchema):
    @post_load
    def make_token(self, data, **kwargs):
        return MetricalFootSeparator.of(data["is_uncertain"]).set_enclosure_type(
            frozenset(data["enclosure_type"])
        )


class GreekLetterSchema(BaseTokenSchema):
    letter = fields.String(required=True, validate=validate.Length(1, 1))
    flags = fields.List(ValueEnumField(Flag), required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return GreekLetter(
            frozenset(data["enclosure_type"]),
            data["erasure"],
            data["letter"],
            data["flags"],
        )


class GreekWordSchema(BaseWordSchema):
    @post_load
    def make_token(self, data, **kwargs):
        return GreekWord.of(
            tuple(data["parts"]),
            data["language"],
            tuple(data["unique_lemma"]),
            data["alignment"],
            data["variant"],
            data["erasure"],
            data["has_variant_alignment"],
            data["has_omitted_alignment"],
        ).set_enclosure_type(frozenset(data["enclosure_type"]))


WORD_SCHEMAS: Mapping[str, Type[BaseWordSchema]] = {
    "Word": WordSchema,
    "LoneDeterminative": LoneDeterminativeSchema,
    "AkkadianWord": AkkadianWordSchema,
    "GreekWord": GreekWordSchema,
}


class OneOfWordSchema(OneOfSchema):
    type_field = "type"
    type_schemas: Mapping[str, Type[BaseWordSchema]] = WORD_SCHEMAS


class OneOfTokenSchema(OneOfSchema):
    type_field = "type"
    type_schemas: Mapping[str, Type[BaseTokenSchema]] = {
        **WORD_SCHEMAS,
        "Token": ValueTokenSchema,
        "ValueToken": ValueTokenSchema,
        "LanguageShift": LanguageShiftSchema,
        "DocumentOrientedGloss": DocumentOrientedGlossSchema,
        "BrokenAway": BrokenAwaySchema,
        "PerhapsBrokenAway": PerhapsBrokenAwaySchema,
        "AccidentalOmission": AccidentalOmissionSchema,
        "IntentionalOmission": IntentionalOmissionSchema,
        "Removal": RemovalSchema,
        "Emendation": EmendationSchema,
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
        "EgyptianMetricalFeetSeparator": EgyptianMetricalFeetSeparatorSchema,
        "LineBreak": LineBreakSchema,
        "Caesura": CaesuraSchema,
        "MetricalFootSeparator": MetricalFootSeparatorSchema,
        "GreekLetter": GreekLetterSchema,
    }
