from typing import Iterable, Sequence, Type

from lark.lexer import Token  # pyre-ignore[21]
from lark.tree import Tree  # pyre-ignore[21]
from lark.visitors import Transformer, v_args  # pyre-ignore[21]

from ebl.transliteration.domain import atf
from ebl.transliteration.domain.atf import Flag, sub_index_to_int
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
    IntentionalOmission,
    LinguisticGloss,
    PerhapsBrokenAway,
    PhoneticGloss,
    Removal,
)
from ebl.transliteration.domain.erasure_visitor import set_erasure_state
from ebl.transliteration.domain.greek_tokens import GreekLetter, GreekWord
from ebl.transliteration.domain.line_number import LineNumber, LineNumberRange
from ebl.transliteration.domain.normalized_akkadian import (
    AkkadianWord,
    Caesura,
    MetricalFootSeparator,
)
from ebl.transliteration.domain.sign_tokens import (
    CompoundGrapheme,
    Divider,
    Grapheme,
    Logogram,
    Number,
    Reading,
)
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import (
    Column,
    CommentaryProtocol,
    Joiner,
    LanguageShift,
    LineBreak,
    Tabulation,
)
from ebl.transliteration.domain.tokens import Token as EblToken
from ebl.transliteration.domain.tokens import UnknownNumberOfSigns, ValueToken, Variant
from ebl.transliteration.domain.unknown_sign_tokens import UnclearSign, UnidentifiedSign
from ebl.transliteration.domain.word_tokens import (
    ErasureState,
    InWordNewline,
    LoneDeterminative,
    Word,
)


def _token_to_list(token):
    if isinstance(token, Tree):
        return token.children
    elif isinstance(token, list):
        return token
    else:
        return [token]


def _children_to_tokens(children: Sequence) -> Sequence[EblToken]:
    return tuple(
        (ValueToken.of(token.value) if isinstance(token, Token) else token)
        for child in children
        for token in _token_to_list(child)
    )


class SignTransformer(Transformer):  # pyre-ignore[11]
    @v_args(inline=True)
    def ebl_atf_text_line__unidentified_sign(self, flags):
        return UnidentifiedSign.of(flags)

    @v_args(inline=True)
    def ebl_atf_text_line__egyptian_metrical_feet_separator(self, flags):
        return EgyptianMetricalFeetSeparator.of(flags)

    @v_args(inline=True)
    def ebl_atf_text_line__unclear_sign(self, flags):
        return UnclearSign.of(flags)

    @v_args(inline=True)
    def ebl_atf_text_line__unknown_number_of_signs(self, _):
        return UnknownNumberOfSigns.of()

    @v_args(inline=True)
    def ebl_atf_text_line__joiner(self, symbol):
        return Joiner.of(atf.Joiner(str(symbol)))

    @v_args(inline=True)
    def ebl_atf_text_line__reading(self, name, sub_index, modifiers, flags, sign=None):
        return Reading.of(tuple(name.children), sub_index, modifiers, flags, sign)

    @v_args()
    def ebl_atf_text_line__value_name_part(self, children):
        return ValueToken.of("".join(children))

    @v_args(inline=True)
    def ebl_atf_text_line__logogram(self, name, sub_index, modifiers, flags, sign=None):
        return Logogram.of(tuple(name.children), sub_index, modifiers, flags, sign)

    @v_args(inline=True)
    def ebl_atf_text_line__surrogate(
        self, name, sub_index, modifiers, flags, surrogate
    ):
        return Logogram.of(
            tuple(name.children), sub_index, modifiers, flags, None, surrogate.children
        )

    @v_args()
    def ebl_atf_text_line__logogram_name_part(self, children):
        return ValueToken.of("".join(children))

    @v_args(inline=True)
    def ebl_atf_text_line__number(self, number, modifiers, flags, sign=None):
        return Number.of(tuple(number.children), modifiers, flags, sign)

    @v_args()
    def ebl_atf_text_line__number_name_head(self, children):
        return ValueToken.of("".join(children))

    @v_args()
    def ebl_atf_text_line__number_name_part(self, children):
        return ValueToken.of("".join(children))

    @v_args(inline=True)
    def ebl_atf_text_line__sub_index(self, sub_index=""):
        return sub_index_to_int(sub_index)

    def ebl_atf_text_line__modifiers(self, tokens):
        return tuple(map(str, tokens))

    def ebl_atf_text_line__flags(self, tokens):
        return tuple(map(atf.Flag, tokens))

    @v_args(inline=True)
    def ebl_atf_text_line__grapheme(self, name, modifiers, flags):
        return Grapheme.of(name.value, modifiers, flags)

    def ebl_atf_text_line__compound_grapheme(self, children):
        return CompoundGrapheme.of([part.value for part in children])


class EnclosureTransformer(Transformer):
    def ebl_atf_text_line__open_accidental_omission(self, _):
        return AccidentalOmission.open()

    def ebl_atf_text_line__close_accidental_omission(self, _):
        return AccidentalOmission.close()

    def ebl_atf_text_line__open_intentional_omission(self, _):
        return IntentionalOmission.open()

    def ebl_atf_text_line__close_intentional_omission(self, _):
        return IntentionalOmission.close()

    def ebl_atf_text_line__open_removal(self, _):
        return Removal.open()

    def ebl_atf_text_line__close_removal(self, _):
        return Removal.close()

    def ebl_atf_text_line__close_broken_away(self, _):
        return BrokenAway.close()

    def ebl_atf_text_line__open_broken_away(self, _):
        return BrokenAway.open()

    def ebl_atf_text_line__close_perhaps_broken_away(self, _):
        return PerhapsBrokenAway.close()

    def ebl_atf_text_line__open_perhaps_broken_away(self, _):
        return PerhapsBrokenAway.open()


class GlossTransformer(Transformer):
    @v_args(inline=True)
    def ebl_atf_text_line__determinative(self, tree):
        tokens = _children_to_tokens(tree.children)
        return Determinative.of(tokens)

    @v_args(inline=True)
    def ebl_atf_text_line__phonetic_gloss(self, tree):
        tokens = _children_to_tokens(tree.children)
        return PhoneticGloss.of(tokens)

    @v_args(inline=True)
    def ebl_atf_text_line__linguistic_gloss(self, tree):
        tokens = _children_to_tokens(tree.children)
        return LinguisticGloss.of(tokens)


class WordTransformer(EnclosureTransformer, GlossTransformer, SignTransformer):
    def _transform_erasure(self, erased, over_erased):
        return [
            Erasure.open(),
            *set_erasure_state(erased, ErasureState.ERASED),
            Erasure.center(),
            *set_erasure_state(over_erased, ErasureState.OVER_ERASED),
            Erasure.close(),
        ]

    def ebl_atf_text_line__lone_determinative(self, children):
        return self._create_word(LoneDeterminative, children)

    def ebl_atf_text_line__word(self, children):
        return self._create_word(Word, children)

    @staticmethod
    def _create_word(word_class: Type[Word], children: Sequence):
        tokens = _children_to_tokens(children)
        return word_class.of(tokens)

    @v_args(inline=True)
    def ebl_atf_text_line__joiner(self, symbol):
        return Joiner.of(atf.Joiner(str(symbol)))

    @v_args(inline=True)
    def ebl_atf_text_line__in_word_newline(self, _):
        return InWordNewline.of()

    def ebl_atf_text_line__variant(self, children):
        tokens = _children_to_tokens(children)
        return Variant.of(*tokens)

    @v_args(inline=True)
    def ebl_atf_text_line__inline_erasure(self, erased, over_erased):
        return self._transform_erasure(erased, over_erased)


class NormalizedAkkadianTransformer(WordTransformer):
    def ebl_atf_text_line__text(self, children) -> Sequence[EblToken]:
        return tuple(children)

    def ebl_atf_text_line__certain_caesura(self, _) -> Caesura:
        return Caesura.certain()

    def ebl_atf_text_line__uncertain_caesura(self, _) -> Caesura:
        return Caesura.uncertain()

    def ebl_atf_text_line__certain_foot_separator(self, _) -> MetricalFootSeparator:
        return MetricalFootSeparator.certain()

    def ebl_atf_text_line__uncertain_foot_separator(self, _) -> MetricalFootSeparator:
        return MetricalFootSeparator.uncertain()

    @v_args(inline=True)  # pyre-ignore[56]
    def ebl_atf_text_line__akkadian_word(
        self,
        parts: Tree,  # pyre-ignore[11]
        modifiers: Sequence[Flag],
        closing_enclosures: Tree,
    ) -> AkkadianWord:
        return AkkadianWord.of(
            tuple(parts.children + closing_enclosures.children), modifiers
        )

    def ebl_atf_text_line__normalized_modifiers(
        self, modifiers: Iterable[Flag]
    ) -> Sequence[Flag]:
        return tuple(set(modifiers))

    @v_args(inline=True)  # pyre-ignore[56]
    def ebl_atf_text_line__normalized_modifier(
        self, modifier: Token  # pyre-ignore[11]
    ) -> Flag:
        return Flag(modifier)

    def ebl_atf_text_line__akkadian_string(
        self, children: Iterable[Token]
    ) -> ValueToken:
        return ValueToken.of("".join(children))

    def ebl_atf_text_line__separator(self, _) -> Joiner:
        return Joiner.hyphen()

    def ebl_atf_text_line__open_emendation(self, _) -> Emendation:
        return Emendation.open()

    def ebl_atf_text_line__close_emendation(self, _) -> Emendation:
        return Emendation.close()


class GreekTransformer(EnclosureTransformer, SignTransformer):
    def ebl_atf_text_line__greek_word(self, children) -> GreekWord:
        return GreekWord.of(
            children.children if isinstance(children, Tree) else children
        )

    @v_args(inline=True)  # pyre-ignore[56]
    def ebl_atf_text_line__greek_letter(self, alphabet, flags) -> GreekLetter:
        return GreekLetter.of(alphabet.value, flags)


class TextLineTransformer(NormalizedAkkadianTransformer, GreekTransformer):
    @v_args(inline=True)
    def text_line(self, line_number, content):
        return TextLine.of_iterable(line_number, content)

    @v_args(inline=True)
    def ebl_atf_text_line__line_number_range(self, start, end):
        return LineNumberRange(start, end)

    @v_args(inline=True)
    def ebl_atf_text_line__single_line_number(
        self, prefix_modifier, number, prime, suffix_modifier
    ):
        return LineNumber(
            int(number), prime is not None, prefix_modifier, suffix_modifier
        )

    def ebl_atf_text_line__text(self, children):
        return _children_to_tokens(children)

    @v_args(inline=True)
    def ebl_atf_text_line__open_document_oriented_gloss(self, _):
        return DocumentOrientedGloss.open()

    @v_args(inline=True)
    def ebl_atf_text_line__close_document_oriented_gloss(self, _):
        return DocumentOrientedGloss.close()

    @v_args(inline=True)
    def ebl_atf_text_line__language_shift(self, value):
        return LanguageShift.of(str(value))

    @v_args(inline=True)
    def ebl_atf_text_line__normalized_akkadian_shift(self, value):
        return LanguageShift.of(str(value))

    @v_args(inline=True)
    def ebl_atf_text_line__greek_shift(self, value):
        return LanguageShift.of(str(value))

    @v_args(inline=True)
    def ebl_atf_text_line__tabulation(self, value):
        return Tabulation.of()

    @v_args(inline=True)
    def ebl_atf_text_line__commentary_protocol(self, value):
        return CommentaryProtocol.of(str(value))

    @v_args(inline=True)
    def ebl_atf_text_line__divider(self, value, modifiers, flags):
        return Divider.of(str(value), modifiers, flags)

    def ebl_atf_text_line__line_break(self, _):
        return LineBreak.of()

    @v_args(inline=True)
    def ebl_atf_text_line__column(self, number):
        return Column.of(number and int(number))

    @v_args(inline=True)
    def ebl_atf_text_line__divider_variant(self, first, second):
        return Variant.of(first, second)

    @v_args(inline=True)
    def ebl_atf_text_line__erasure(self, erased, over_erased):
        return self._transform_erasure(erased, over_erased)
