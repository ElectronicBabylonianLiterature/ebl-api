from typing import Sequence, Type

from lark.visitors import v_args
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.enclosure_transformer import (
    EnclosureTransformer,
    GlossTransformer,
)
from ebl.transliteration.domain.lark import tokens_to_value_tokens
from ebl.transliteration.domain.signs_transformer import SignTransformer
from ebl.transliteration.domain.tokens import Variant
from ebl.transliteration.domain.word_tokens import (
    InWordNewline,
    LoneDeterminative,
    Word,
)


class WordTransformer(EnclosureTransformer, GlossTransformer, SignTransformer):
    def lone_determinative(self, children):
        return self._create_word(LoneDeterminative, children)

    def word(self, children):
        return self._create_word(Word, children)

    @staticmethod
    def _create_word(word_class: Type[Word], children: Sequence):
        tokens = tokens_to_value_tokens(children)
        return word_class.of(tokens)

    @v_args(inline=True)
    def joiner(self, symbol):
        return atf.Joiner.of(atf.Joiner(str(symbol)))

    @v_args(inline=True)
    def in_word_newline(self, _):
        return InWordNewline.of()

    def variant(self, children):
        tokens = tokens_to_value_tokens(children)
        return Variant.of(*tokens)

    @v_args(inline=True)
    def inline_erasure(self, erased, over_erased):
        return self._transform_erasure(erased, over_erased)
