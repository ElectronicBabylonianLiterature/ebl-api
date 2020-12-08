from typing import Optional

from marshmallow import Schema, fields, post_load  # pyre-ignore[21]

from ebl.transliteration.domain.word_tokens import AbstractWord
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.lark_parser import (
    parse_normalized_akkadian_word,
    parse_word,
)

from ebl.transliteration.domain.alignment import AlignmentToken
from ebl.corpus.domain.alignment import Alignment, ManuscriptLineAlignment


class AlignmentTokenSchema(Schema):  # pyre-ignore[11]
    value = fields.String(required=True)
    alignment = fields.Integer(missing=None)
    variant = fields.String(missing="", load_only=True)
    language = fields.String(missing="", load_only=True)
    isNormalized = fields.Boolean(missing=False, load_only=True)

    @post_load  # pyre-ignore[56]
    def make_alignment_token(self, data: dict, **kwargs) -> AlignmentToken:
        return AlignmentToken(data["value"], data["alignment"], self._create_word(data))

    @staticmethod
    def _create_word(data: dict) -> Optional[AbstractWord]:
        variant = data.get("variant")
        if variant:
            language = Language[data["language"]]
            is_normalized = data["isNormalized"]

            return (
                parse_normalized_akkadian_word(variant)
                if language is Language.AKKADIAN and is_normalized
                else parse_word(variant).set_language(language, is_normalized)
            )
        else:
            return None


class ManuscriptAlignmentSchema(Schema):
    alignment = fields.Nested(AlignmentTokenSchema, many=True, required=True)
    omitted_words = fields.List(
        fields.Integer(), required=True, data_key="omittedWords"
    )

    @post_load  # pyre-ignore[56]
    def make_manuscript_alignment(
        self, data: dict, **kwargs
    ) -> ManuscriptLineAlignment:
        return ManuscriptLineAlignment(
            tuple(data["alignment"]), tuple(data["omitted_words"])
        )


class AlignmentSchema(Schema):
    lines = fields.List(
        fields.Nested(ManuscriptAlignmentSchema, many=True),
        required=True,
        data_key="alignment",
    )

    @post_load  # pyre-ignore[56]
    def make_alignment(self, data: dict, **kwargs) -> Alignment:
        return Alignment(tuple(tuple(line) for line in data["lines"]))
