from typing import Sequence

from lark.exceptions import ParseError, UnexpectedInput

from ebl.transliteration.domain.atf_parsers.lark_parser import LINE_PARSER
from ebl.transliteration.domain.normalized_akkadian import AkkadianWord, Break
from ebl.transliteration.domain.text_line_transformer import TextLineTransformer
from ebl.transliteration.domain.tokens import Token

RECONSTRUCTED_LINE_PARSER = LINE_PARSER


def parse_reconstructed_word(word: str) -> AkkadianWord:
    tree = RECONSTRUCTED_LINE_PARSER.parse(
        word, start="ebl_atf_text_line__akkadian_word"
    )
    return TextLineTransformer().transform(tree)


def parse_break(break_: str) -> Break:
    tree = RECONSTRUCTED_LINE_PARSER.parse(break_, start="ebl_atf_text_line__break")
    return TextLineTransformer().transform(tree)


def parse_reconstructed_line(text: str) -> Sequence[Token]:
    try:
        tree = RECONSTRUCTED_LINE_PARSER.parse(text, start="ebl_atf_text_line__text")
        return TextLineTransformer().transform(tree)
    except (UnexpectedInput, ParseError) as error:
        raise ValueError(f"Invalid reconstructed line: {text}. {error}")
