from typing import Callable, Mapping, Optional, TypeVar

from marshmallow import Schema, fields, post_load, ValidationError

from ebl.corpus.domain.alignment import Alignment, ManuscriptLineAlignment
from ebl.transliteration.domain.alignment import AlignmentToken
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.atf_parsers.lark_parser import (
    parse_greek_word,
    parse_normalized_akkadian_word,
    parse_word,
)
from ebl.transliteration.domain.atf_parsers.lark_parser_errors import PARSE_ERRORS
from ebl.transliteration.domain.word_tokens import AbstractWord


VariantParser = Callable[[str, Language], AbstractWord]
VARIANT_PARSERS: Mapping[str, VariantParser] = {
    "Word": lambda atf, language: parse_word(atf).set_language(language),
    "AkkadianWord": lambda atf, _: parse_normalized_akkadian_word(atf),
    "GreekWord": lambda atf, language: parse_greek_word(atf).set_language(language),
}
T = TypeVar("T")


def _find_variant_option(options: Mapping[str, T], data: dict, field: str) -> T:
    try:
        return options[data[field]]
    except KeyError as error:
        raise ValidationError(f"Invalid {field} {data[field]}.", field) from error


class AlignmentTokenSchema(Schema):
    value = fields.String(required=True)
    alignment = fields.Integer(load_default=None)
    variant = fields.String(load_default="", load_only=True)
    type = fields.String(load_default="", load_only=True)
    language = fields.String(load_default="", load_only=True)

    @post_load
    def make_alignment_token(self, data: dict, **kwargs) -> AlignmentToken:
        return AlignmentToken(
            data["value"], data["alignment"], self._create_variant(data)
        )

    @staticmethod
    def _create_variant(data: dict) -> Optional[AbstractWord]:
        return AlignmentTokenSchema._parse_variant(data) if data["variant"] else None

    @staticmethod
    def _parse_variant(data: dict) -> AbstractWord:
        language = _find_variant_option(Language.__members__, data, "language")
        parse = _find_variant_option(VARIANT_PARSERS, data, "type")
        try:
            return parse(data["variant"], language)
        except PARSE_ERRORS as error:
            raise ValidationError(
                f"Invalid value {data['variant']} for {data['type']}.", "variant"
            ) from error


class ManuscriptAlignmentSchema(Schema):
    alignment = fields.Nested(AlignmentTokenSchema, many=True, required=True)
    omitted_words = fields.List(
        fields.Integer(), required=True, data_key="omittedWords"
    )

    @post_load
    def make_manuscript_alignment(
        self, data: dict, **kwargs
    ) -> ManuscriptLineAlignment:
        return ManuscriptLineAlignment(
            tuple(data["alignment"]), tuple(data["omitted_words"])
        )


class AlignmentSchema(Schema):
    lines = fields.List(
        fields.List(fields.Nested(ManuscriptAlignmentSchema, many=True)),
        required=True,
        data_key="alignment",
    )

    @post_load
    def make_alignment(self, data: dict, **kwargs) -> Alignment:
        return Alignment(
            tuple(tuple(tuple(variant) for variant in line) for line in data["lines"])
        )
