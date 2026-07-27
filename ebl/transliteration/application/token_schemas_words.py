from typing import Callable, Dict, Sequence

import pydash
from marshmallow import fields, post_dump, post_load, validate

from ebl.schemas import NameEnumField, ValueEnumField
from ebl.transliteration.application.token_schemas_enclosures import BaseTokenSchema
from ebl.transliteration.domain.atf import Flag
from ebl.transliteration.domain.greek_tokens import GreekLetter, GreekWord
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.normalized_akkadian import (
    AkkadianWord,
    Caesura,
    MetricalFootSeparator,
)
from ebl.transliteration.domain.tokens import Token
from ebl.transliteration.domain.word_tokens import (
    AbstractWord,
    LoneDeterminative,
    Word,
)


def shared_word_arguments(data: dict) -> Dict[str, object]:
    return {
        "unique_lemma": tuple(data["unique_lemma"]),
        "alignment": data["alignment"],
        "variant": data["variant"],
        "has_variant_alignment": data["has_variant_alignment"],
        "has_omitted_alignment": data["has_omitted_alignment"],
        "id_": data.get("id_"),
        "named_entities": tuple(data.get("named_entities", [])),
        "realia": tuple(data.get("realia", [])),
    }


def load_word(
    factory: Callable[..., AbstractWord],
    parts: Sequence[Token],
    data: dict,
    **arguments: object,
) -> AbstractWord:
    return factory(
        parts, **arguments, **shared_word_arguments(data)
    ).set_enclosure_type(frozenset(data["enclosure_type"]))


class BaseWordSchema(BaseTokenSchema):
    parts = fields.List(fields.Nested("OneOfTokenSchema"), required=True)
    language = NameEnumField(Language, required=True)
    normalized = fields.Boolean(required=True)
    lemmatizable = fields.Boolean(required=True)
    alignable = fields.Boolean()
    unique_lemma = fields.List(fields.String(), data_key="uniqueLemma", required=True)
    alignment = fields.Integer(allow_none=True, load_default=None)
    variant = fields.Nested("OneOfWordSchema", allow_none=True, load_default=None)
    has_variant_alignment = fields.Boolean(
        load_default=False, data_key="hasVariantAlignment"
    )
    has_omitted_alignment = fields.Boolean(
        load_default=False, data_key="hasOmittedAlignment"
    )
    id_ = fields.String(data_key="id", allow_none=True)
    named_entities = fields.List(
        fields.String(),
        data_key="namedEntities",
        dump_default=(),
        load_default=(),
    )
    realia = fields.List(
        fields.String(),
        data_key="realia",
        dump_default=(),
        load_default=(),
    )


class AbstractWordSchema(BaseWordSchema):
    @post_dump
    def dump_token(self, data, **kwargs):
        return pydash.omit_by(data, lambda value: value is None)


class WordSchema(AbstractWordSchema):
    @post_load
    def make_token(self, data, **kwargs):
        return load_word(
            Word.of,
            data["parts"],
            data,
            language=data["language"],
            erasure=data["erasure"],
        )


class LoneDeterminativeSchema(AbstractWordSchema):
    @post_load
    def make_token(self, data, **kwargs):
        return load_word(
            LoneDeterminative.of,
            data["parts"],
            data,
            language=data["language"],
            erasure=data["erasure"],
        )


class AkkadianWordSchema(BaseWordSchema):
    modifiers = fields.List(ValueEnumField(Flag), required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return load_word(
            AkkadianWord.of,
            tuple(data["parts"]),
            data,
            modifier=tuple(data["modifiers"]),
        )


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
        return load_word(
            GreekWord.of,
            tuple(data["parts"]),
            data,
            language=data["language"],
            erasure=data["erasure"],
        )
