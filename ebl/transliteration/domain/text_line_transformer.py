from typing import Iterable, Sequence, Type

from lark.lexer import Token
from lark.tree import Tree
from lark.visitors import v_args
import pydash

from ebl.transliteration.domain import atf
from ebl.transliteration.domain.add_namespace import add_namespace
from ebl.transliteration.domain.atf import Flag
from ebl.transliteration.domain.enclosure_tokens import Emendation
from ebl.transliteration.domain.enclosure_transformer import (
    EnclosureTransformer,
    GlossTransformer,
)
from ebl.transliteration.domain.greek_tokens import GreekLetter, GreekWord
from ebl.transliteration.domain.lark import tokens_to_value_tokens
from ebl.transliteration.domain.line_number import LineNumber, LineNumberRange
from ebl.transliteration.domain.line_number_transformer import LineNumberTransformer
from ebl.transliteration.domain.normalized_akkadian import (
    AkkadianWord,
    Caesura,
    MetricalFootSeparator,
)
from ebl.transliteration.domain.sign_tokens import Divider
from ebl.transliteration.domain.signs_transformer import SignTransformer
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.text_transformer import TextTransformer
from ebl.transliteration.domain.tokens import (
    Column,
    CommentaryProtocol,
    Joiner,
    LanguageShift,
    LineBreak,
    Tabulation,
    WordOmitted,
)
from ebl.transliteration.domain.tokens import Token as EblToken
from ebl.transliteration.domain.tokens import ValueToken, Variant
from ebl.transliteration.domain.word_tokens import (
    InWordNewline,
    LoneDeterminative,
    Word,
)
from ebl.transliteration.domain.word_transformer import WordTransformer


# class WordTransformer(EnclosureTransformer, GlossTransformer, SignTransformer):
#     def text_line__lone_determinative(self, children):
#         return self._create_word(LoneDeterminative, children)

#     def text_line__word(self, children):
#         return self._create_word(Word, children)

#     @staticmethod
#     def _create_word(word_class: Type[Word], children: Sequence):
#         tokens = tokens_to_value_tokens(children)
#         return word_class.of(tokens)

#     @v_args(inline=True)
#     def text_line__joiner(self, symbol):
#         return Joiner.of(atf.Joiner(str(symbol)))

#     @v_args(inline=True)
#     def text_line__in_word_newline(self, _):
#         return InWordNewline.of()

#     def text_line__variant(self, children):
#         tokens = tokens_to_value_tokens(children)
#         return Variant.of(*tokens)

#     @v_args(inline=True)
#     def text_line__inline_erasure(self, erased, over_erased):
#         return self._transform_erasure(erased, over_erased)


class NormalizedAkkadianTransformer(EnclosureTransformer, SignTransformer):
    def text_line__text(self, children) -> Sequence[EblToken]:
        return tuple(children)

    def text_line__certain_caesura(self, _) -> Caesura:
        return Caesura.certain()

    def text_line__uncertain_caesura(self, _) -> Caesura:
        return Caesura.uncertain()

    def text_line__certain_foot_separator(self, _) -> MetricalFootSeparator:
        return MetricalFootSeparator.certain()

    def text_line__uncertain_foot_separator(self, _) -> MetricalFootSeparator:
        return MetricalFootSeparator.uncertain()

    @v_args(inline=True)
    def text_line__akkadian_word(
        self, parts: Tree, modifiers: Sequence[Flag], closing_enclosures: Tree
    ) -> AkkadianWord:
        return AkkadianWord.of(
            tuple(parts.children + closing_enclosures.children), modifiers
        )

    def text_line__normalized_modifiers(
        self, modifiers: Iterable[Flag]
    ) -> Sequence[Flag]:
        return tuple(pydash.uniq(modifiers))

    @v_args(inline=True)
    def text_line__normalized_modifier(self, modifier: Token) -> Flag:
        return Flag(modifier)

    def text_line__akkadian_string(self, children: Iterable[Token]) -> ValueToken:
        return ValueToken.of("".join(children))  # pyre-ignore[6]

    def text_line__separator(self, _) -> Joiner:
        return Joiner.hyphen()

    def text_line__open_emendation(self, _) -> Emendation:
        return Emendation.open()

    def text_line__close_emendation(self, _) -> Emendation:
        return Emendation.close()


class GreekTransformer(EnclosureTransformer, SignTransformer):
    def text_line__greek_word(self, children) -> GreekWord:
        return GreekWord.of(
            children.children if isinstance(children, Tree) else children
        )

    @v_args(inline=True)
    def text_line__greek_letter(self, alphabet, flags) -> GreekLetter:
        return GreekLetter.of(alphabet.value, flags)


class TextLineTransformer(
    add_namespace(WordTransformer, "text_line__text"),
    add_namespace(TextTransformer, "text_line"),
    NormalizedAkkadianTransformer,
    GreekTransformer,
    add_namespace(LineNumberTransformer, "text_line__line_number"),
):
    @v_args(inline=True)
    def text_line(self, line_number, content):
        return TextLine.of_iterable(line_number, content)

    # @v_args(inline=True)
    # def text_line__line_number_range(self, start, end):
    #     return LineNumberRange(start, end)

    # @v_args(inline=True)
    # def text_line__line_number__single_line_number(
    #     self, prefix_modifier, number, prime, suffix_modifier
    # ):
    #     return LineNumber(
    #         int(number), prime is not None, prefix_modifier, suffix_modifier
    #     )

    # def text_line__text(self, children):
    #     return tokens_to_value_tokens(children)

    @v_args(inline=True)
    def text_line__language_shift(self, value):
        return LanguageShift.of(str(value))

    @v_args(inline=True)
    def text_line__normalized_akkadian_shift(self, value):
        return LanguageShift.of(str(value))

    @v_args(inline=True)
    def text_line__greek_shift(self, value):
        return LanguageShift.of(str(value))

    @v_args(inline=True)
    def text_line__word_omitted(self, value):
        return WordOmitted.of()

    @v_args(inline=True)
    def text_line__tabulation(self, value):
        return Tabulation.of()

    @v_args(inline=True)
    def text_line__commentary_protocol(self, value):
        return CommentaryProtocol.of(str(value))

    @v_args(inline=True)
    def text_line__divider(self, value, modifiers, flags):
        return Divider.of(str(value), modifiers, flags)

    def text_line__line_break(self, _):
        return LineBreak.of()

    @v_args(inline=True)
    def text_line__column_token(self, number):
        return Column.of(number and int(number))

    @v_args(inline=True)
    def text_line__divider_variant(self, first, second):
        return Variant.of(first, second)
