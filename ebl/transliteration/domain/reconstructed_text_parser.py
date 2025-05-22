from typing import Sequence

from lark.exceptions import ParseError, UnexpectedInput
from lark.lark import Lark

from ebl.transliteration.domain.normalized_akkadian import AkkadianWord, Break
from ebl.transliteration.domain.text_line_transformer import TextLineTransformer
from ebl.transliteration.domain.tokens import Token

RECONSTRUCTED_LINE_PARSER = Lark.open(
    "ebl_atf.lark",
    maybe_placeholders=True,
    rel_to=__file__,
    start="ebl_atf__text_line__text",
)


def parse_reconstructed_word(word: str) -> AkkadianWord:
    tree = RECONSTRUCTED_LINE_PARSER.parse(
        word, start="ebl_atf__text_line__akkadian_word"
    )
    return TextLineTransformer().transform(tree)


def parse_break(break_: str) -> Break:
    tree = RECONSTRUCTED_LINE_PARSER.parse(break_, start="ebl_atf__text_line__break")
    return TextLineTransformer().transform(tree)


def parse_reconstructed_line(text: str) -> Sequence[Token]:
    try:
        tree = RECONSTRUCTED_LINE_PARSER.parse(text)
        return TextLineTransformer().transform(tree)
    except (UnexpectedInput, ParseError) as error:
        raise ValueError(f"Invalid reconstructed line: {text}. {error}")
