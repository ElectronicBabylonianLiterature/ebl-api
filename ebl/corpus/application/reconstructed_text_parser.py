from typing import Iterable, Sequence

from lark.lexer import Token  # pyre-ignore[21]
from lark.tree import Tree
from lark.visitors import Transformer, v_args
from lark.lark import Lark
from lark.exceptions import ParseError, UnexpectedInput

from ebl.corpus.domain.enclosure import Enclosure, EnclosureType, EnclosureVariant
from ebl.corpus.domain.reconstructed_text import (
    AkkadianWord,
    Caesura,
    EnclosurePart,
    Lacuna,
    LacunaPart,
    MetricalFootSeparator,
    Modifier,
    Part,
    ReconstructionToken,
    SeparatorPart,
    StringPart,
)


class ReconstructedLineTransformer(Transformer):  # pyre-ignore[11]
    def reconstructed_line(
        self, children: Iterable[ReconstructionToken]
    ) -> Sequence[ReconstructionToken]:
        return tuple(children)

    def certain_caesura(self, _) -> Caesura:
        return Caesura(False)

    def uncertain_caesura(self, _) -> Caesura:
        return Caesura(True)

    def certain_foot_separator(self, _) -> MetricalFootSeparator:
        return MetricalFootSeparator(False)

    def uncertain_foot_separator(self, _) -> MetricalFootSeparator:
        return MetricalFootSeparator(True)

    @v_args(inline=True)
    def lacuna(self, before: Tree, after: Tree) -> Lacuna:  # pyre-ignore[11]
        return Lacuna(tuple(before.children), tuple(after.children))

    @v_args(inline=True)
    def akkadian_word(
        self,
        parts: Tree,  # pyre-ignore[11]
        modifiers: Sequence[Modifier],
        closing_enclosures: Tree,  # pyre-ignore[11]
    ) -> AkkadianWord:
        return AkkadianWord(
            tuple(parts.children + closing_enclosures.children), modifiers
        )

    def modifiers(self, modifiers: Iterable[Modifier]) -> Sequence[Modifier]:
        return tuple(set(modifiers))

    @v_args(inline=True)
    def modifier(self, modifier: Token) -> Modifier:  # pyre-ignore[11]
        return Modifier(modifier)

    def lacuna_part(self, _) -> LacunaPart:
        return LacunaPart()

    def akkadian_string(
        self, children: Iterable[Token]  # pyre-ignore[11]
    ) -> StringPart:
        return StringPart("".join(children))

    def separator(self, _) -> SeparatorPart:
        return SeparatorPart()

    @v_args(inline=True)
    def enclosure_open(self, enclosure: Enclosure) -> EnclosurePart:
        return EnclosurePart(enclosure)

    @v_args(inline=True)
    def enclosure_close(self, enclosure: Enclosure) -> EnclosurePart:
        return EnclosurePart(enclosure)

    def broken_off_open(self, _) -> Enclosure:
        return Enclosure(EnclosureType.BROKEN_OFF, EnclosureVariant.OPEN)

    def broken_off_close(self, _) -> Enclosure:
        return Enclosure(EnclosureType.BROKEN_OFF, EnclosureVariant.CLOSE)

    def maybe_broken_off_open(self, _) -> Enclosure:
        return Enclosure(EnclosureType.MAYBE_BROKEN_OFF, EnclosureVariant.OPEN)

    def maybe_broken_off_close(self, _) -> Enclosure:
        return Enclosure(EnclosureType.MAYBE_BROKEN_OFF, EnclosureVariant.CLOSE)

    def emendation_open(self, _) -> Enclosure:
        return Enclosure(EnclosureType.EMENDATION, EnclosureVariant.OPEN)

    def emendation_close(self, _) -> Enclosure:
        return Enclosure(EnclosureType.EMENDATION, EnclosureVariant.CLOSE)


RECONSTRUCTED_LINE_PARSER = Lark.open(
    "reconstructed_line.lark", maybe_placeholders=True, rel_to=__file__
)


def parse_reconstructed_word(word: str) -> Sequence[Part]:
    tree = RECONSTRUCTED_LINE_PARSER.parse(word, start="akkadian_word")
    return ReconstructedLineTransformer().transform(tree)  # pyre-ignore[16]


def parse_lacuna(lacuna: str) -> Sequence[Part]:
    tree = RECONSTRUCTED_LINE_PARSER.parse(lacuna, start="lacuna")
    return ReconstructedLineTransformer().transform(tree)  # pyre-ignore[16]


def parse_break(break_: str) -> Sequence[Part]:
    tree = RECONSTRUCTED_LINE_PARSER.parse(break_, start="break")
    return ReconstructedLineTransformer().transform(tree)  # pyre-ignore[16]


def parse_reconstructed_line(text: str) -> Sequence[ReconstructionToken]:
    try:
        tree = RECONSTRUCTED_LINE_PARSER.parse(text)
        return ReconstructedLineTransformer().transform(tree)  # pyre-ignore[16]
    except (UnexpectedInput, ParseError) as error:
        raise ValueError(f"Invalid reconstructed line: {text}. {error}")
