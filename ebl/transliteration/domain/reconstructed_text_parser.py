from typing import Sequence

from lark.lark import Lark  # pyre-ignore[21]
from lark.exceptions import ParseError, UnexpectedInput

from ebl.transliteration.domain.reconstructed_text import (
    AkkadianWord,
    Break,
    Lacuna,
    ReconstructionToken,
)
from ebl.transliteration.domain.text_line_transformer import TextLineTransformer


RECONSTRUCTED_LINE_PARSER = Lark.open(
    "ebl_atf.lark",
    maybe_placeholders=True,
    rel_to=__file__,
    start="ebl_atf_text_line__text",
)


def parse_reconstructed_word(word: str) -> AkkadianWord:
    tree = RECONSTRUCTED_LINE_PARSER.parse(
        word, start="ebl_atf_text_line__akkadian_word"
    )
    return TextLineTransformer().transform(tree)  # pyre-ignore[16]


def parse_lacuna(lacuna: str) -> Lacuna:
    tree = RECONSTRUCTED_LINE_PARSER.parse(lacuna, start="ebl_atf_text_line__lacuna")
    return TextLineTransformer().transform(tree)  # pyre-ignore[16]


def parse_break(break_: str) -> Break:
    tree = RECONSTRUCTED_LINE_PARSER.parse(break_, start="ebl_atf_text_line__break")
    return TextLineTransformer().transform(tree)  # pyre-ignore[16]


def parse_reconstructed_line(text: str) -> Sequence[ReconstructionToken]:
    try:
        tree = RECONSTRUCTED_LINE_PARSER.parse(text)
        return TextLineTransformer().transform(tree)  # pyre-ignore[16]
    except (UnexpectedInput, ParseError) as error:
        raise ValueError(f"Invalid reconstructed line: {text}. {error}")
