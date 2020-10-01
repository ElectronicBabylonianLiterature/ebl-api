from typing import Iterable, Optional, Sequence

from lark.lexer import Token  # pyre-ignore[21]
from lark.tree import Tree
from lark.visitors import Transformer, v_args
import pydash  # pyre-ignore[21]
from parsy import (  # pyre-ignore[21]
    ParseError,
    alt,
    char_from,
    from_enum,
    seq,
    string,
    string_from,
)

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
from lark.lark import Lark

ELLIPSIS = string("...")


def enclosure_side(type_: EnclosureType, variant: EnclosureVariant):
    return string(type_.get_delimiter(variant)).map(lambda _: Enclosure(type_, variant))


def enclosure(variant: Optional[EnclosureVariant] = None):
    variants = [variant] if variant else [variant for variant in EnclosureVariant]
    sides = [
        enclosure_side(type_, variant)
        for type_ in EnclosureType
        for variant in variants
    ]
    return alt(*sides)


def akkadian_string():
    akkadian_alphabet = char_from(
        "ʾABDEGHIKLMNPSTUYZabcdefghiklmnpqrstuwyzÉâêîûāĒēīŠšūṣṭ₄"
    )
    return akkadian_alphabet.at_least(1).concat()


def akkadian_word():
    separator_part = string("-").map(lambda _: SeparatorPart())
    broken_off_open_part = enclosure(EnclosureVariant.OPEN).map(EnclosurePart)
    broken_off_close_part = enclosure(EnclosureVariant.CLOSE).map(EnclosurePart)
    broken_off_part = enclosure().map(EnclosurePart)
    lacuna_part = ELLIPSIS.map(lambda _: LacunaPart())
    string_part = akkadian_string().map(StringPart)
    between_strings = (
        seq(broken_off_part.at_least(1), separator_part)
        | seq(separator_part, broken_off_part.at_least(1))
        | broken_off_part.at_least(1)
        | separator_part
    )
    modifier = from_enum(Modifier)
    return (
        seq(
            broken_off_open_part.many(),
            seq(lacuna_part, between_strings.optional()).optional(),
            string_part,
            (
                seq(between_strings, string_part | lacuna_part)
                | seq(lacuna_part, between_strings.optional(), string_part)
                | string_part
            ).many(),
            seq(between_strings.optional(), lacuna_part).optional(),
        ).map(pydash.flatten_deep)
        + seq(
            modifier.at_most(3).map(pydash.uniq).map(lambda f: [f]),
            broken_off_close_part.many(),
        )
        .map(pydash.reverse)
        .map(pydash.flatten)
    ).map(pydash.partial_right(pydash.reject, pydash.is_none))


def lacuna():
    return seq(
        enclosure(EnclosureVariant.OPEN).many(),
        ELLIPSIS,
        enclosure(EnclosureVariant.CLOSE).many(),
    )


CAESURA = "||"


def caesura():
    return string_from(f"({CAESURA})", CAESURA)


FOOT_SEPARATOR = "|"


def foot_separator():
    return string_from(f"({FOOT_SEPARATOR})", FOOT_SEPARATOR)


def reconstructed_line():
    break_ = caesura().map(
        lambda token: Caesura(False) if token == CAESURA else Caesura(True)
    ) | foot_separator().map(
        lambda token: MetricalFootSeparator(False)
        if token == FOOT_SEPARATOR
        else MetricalFootSeparator(True)
    )
    word_separator = string(" ")
    text_part = (
        (
            akkadian_word().map(
                lambda token: AkkadianWord(tuple(token[:-1]), tuple(token[-1]))
            )
            | lacuna().map(lambda token: Lacuna(tuple(token[0]), tuple(token[2])))
        )
        .at_least(1)
        .sep_by(word_separator)
    )

    return (
        text_part + seq(word_separator >> break_ << word_separator, text_part).many()
    ).map(pydash.flatten_deep)


class ReconstructedLineTransformer(Transformer):  # pyre-ignore[11]
    @v_args(inline=True)
    def lacuna(self, before, after) -> Lacuna:
        return Lacuna(before, after)

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
    def modifier(self, modifier) -> Modifier:
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
    def enclosure_open(self, enclosure) -> EnclosurePart:
        return EnclosurePart(enclosure)

    @v_args(inline=True)
    def enclosure_close(self, enclosure) -> EnclosurePart:
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


def parse_reconstructed_line(text: str) -> Sequence[ReconstructionToken]:
    try:
        return tuple(reconstructed_line().parse(text))
    except ParseError as error:
        raise ValueError(f"Invalid reconstructed line: {text}. {error}")
