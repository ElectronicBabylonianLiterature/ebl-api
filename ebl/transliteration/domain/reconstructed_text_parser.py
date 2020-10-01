from typing import Iterable, Sequence

from lark.lexer import Token  # pyre-ignore[21]
from lark.tree import Tree
from lark.visitors import Transformer, v_args
from lark.lark import Lark
from lark.exceptions import ParseError, UnexpectedInput

from ebl.transliteration.domain.reconstructed_text import (
    AkkadianWord,
    Break,
    Caesura,
    Lacuna,
    MetricalFootSeparator,
    ReconstructionToken,
)
from ebl.transliteration.domain.atf import Flag
from ebl.transliteration.domain.tokens import Joiner, UnknownNumberOfSigns, ValueToken
from ebl.transliteration.domain.enclosure_tokens import (
    BrokenAway,
    Emendation,
    PerhapsBrokenAway,
)


class ReconstructedLineTransformer(Transformer):  # pyre-ignore[11]
    def normalized_akkadian(
        self, children: Iterable[ReconstructionToken]
    ) -> Sequence[ReconstructionToken]:
        return tuple(children)

    def certain_caesura(self, _) -> Caesura:
        return Caesura.certain()

    def uncertain_caesura(self, _) -> Caesura:
        return Caesura.uncertain()

    def certain_foot_separator(self, _) -> MetricalFootSeparator:
        return MetricalFootSeparator.certain()

    def uncertain_foot_separator(self, _) -> MetricalFootSeparator:
        return MetricalFootSeparator.uncertain()

    @v_args(inline=True)
    def lacuna(self, before: Tree, _, after: Tree) -> Lacuna:  # pyre-ignore[11]
        return Lacuna.of(tuple(before.children), tuple(after.children))

    @v_args(inline=True)
    def akkadian_word(
        self,
        parts: Tree,  # pyre-ignore[11]
        modifiers: Sequence[Flag],
        closing_enclosures: Tree,  # pyre-ignore[11]
    ) -> AkkadianWord:
        return AkkadianWord.of(
            tuple(parts.children + closing_enclosures.children), modifiers
        )

    def normalized_modifiers(self, modifiers: Iterable[Flag]) -> Sequence[Flag]:
        return tuple(set(modifiers))

    @v_args(inline=True)
    def normalized_modifier(self, modifier: Token) -> Flag:  # pyre-ignore[11]
        return Flag(modifier)

    def akkadian_string(
        self, children: Iterable[Token]  # pyre-ignore[11]
    ) -> ValueToken:
        return ValueToken.of("".join(children))

    def separator(self, _) -> Joiner:
        return Joiner.hyphen()

    def unknown_number_of_signs(self, _) -> UnknownNumberOfSigns:
        return UnknownNumberOfSigns.of()

    def open_broken_away(self, _) -> BrokenAway:
        return BrokenAway.open()

    def close_broken_away(self, _) -> BrokenAway:
        return BrokenAway.close()

    def open_perhaps_broken_away(self, _) -> PerhapsBrokenAway:
        return PerhapsBrokenAway.open()

    def close_perhaps_broken_away(self, _) -> PerhapsBrokenAway:
        return PerhapsBrokenAway.close()

    def open_emendation(self, _) -> Emendation:
        return Emendation.open()

    def close_emendation(self, _) -> Emendation:
        return Emendation.close()


RECONSTRUCTED_LINE_PARSER = Lark.open(
    "ebl_atf_text_line.lark",
    maybe_placeholders=True,
    rel_to=__file__,
    start="normalized_akkadian",
)


def parse_reconstructed_word(word: str) -> AkkadianWord:
    tree = RECONSTRUCTED_LINE_PARSER.parse(word, start="akkadian_word")
    return ReconstructedLineTransformer().transform(tree)  # pyre-ignore[16]


def parse_lacuna(lacuna: str) -> Lacuna:
    tree = RECONSTRUCTED_LINE_PARSER.parse(lacuna, start="lacuna")
    return ReconstructedLineTransformer().transform(tree)  # pyre-ignore[16]


def parse_break(break_: str) -> Break:
    tree = RECONSTRUCTED_LINE_PARSER.parse(break_, start="break")
    return ReconstructedLineTransformer().transform(tree)  # pyre-ignore[16]


def parse_reconstructed_line(text: str) -> Sequence[ReconstructionToken]:
    try:
        tree = RECONSTRUCTED_LINE_PARSER.parse(text, start="normalized_akkadian")
        return ReconstructedLineTransformer().transform(tree)  # pyre-ignore[16]
    except (UnexpectedInput, ParseError) as error:
        raise ValueError(f"Invalid reconstructed line: {text}. {error}")
