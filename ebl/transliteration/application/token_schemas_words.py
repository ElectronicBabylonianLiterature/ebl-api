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
from ebl.transliteration.domain.word_tokens import (
    LoneDeterminative,
    Word,
)


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
            data.get("id_"),
            tuple(data.get("named_entities", [])),
            tuple(data.get("realia", [])),
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
            data.get("id_"),
            tuple(data.get("named_entities", [])),
            tuple(data.get("realia", [])),
        ).set_enclosure_type(frozenset(data["enclosure_type"]))

    @post_dump
    def dump_token(self, data, **kwargs):
        return pydash.omit_by(data, lambda value: value is None)


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
            data.get("id_"),
            tuple(data.get("named_entities", [])),
            tuple(data.get("realia", [])),
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
            data.get("id_"),
            tuple(data.get("named_entities", [])),
            tuple(data.get("realia", [])),
        ).set_enclosure_type(frozenset(data["enclosure_type"]))
