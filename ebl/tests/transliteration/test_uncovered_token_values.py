import pytest

from ebl.transliteration.domain import atf
from ebl.transliteration.domain.atf_parsers.lark_parser import parse_atf_lark
from ebl.transliteration.domain.markup import ParagraphPart, UrlPart
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import Joiner


@pytest.mark.parametrize(
    "joiner,expected",
    [
        (Joiner.hyphen(), atf.Joiner.HYPHEN),
        (Joiner.dot(), atf.Joiner.DOT),
        (Joiner.plus(), atf.Joiner.PLUS),
        (Joiner.colon(), atf.Joiner.COLON),
        (Joiner.semicolon(), atf.Joiner.SEMICOLON),
        (Joiner.comma(), atf.Joiner.COMMA),
    ],
)
def test_each_joiner_constructor_uses_its_own_symbol(joiner, expected) -> None:
    assert joiner == Joiner.of(expected)
    assert joiner.value == expected.value


def test_every_joiner_constructor_is_distinct() -> None:
    joiners = [
        Joiner.hyphen(),
        Joiner.dot(),
        Joiner.plus(),
        Joiner.colon(),
        Joiner.semicolon(),
        Joiner.comma(),
    ]

    assert len({joiner.value for joiner in joiners}) == len(joiners)


def test_a_paragraph_part_renders_as_a_blank_line() -> None:
    assert ParagraphPart().value == "\n\n"


def test_a_url_part_with_text_renders_both_braces() -> None:
    assert UrlPart("here", "https://example.org").value == (
        "@url{https://example.org}{here}"
    )


def test_a_url_part_without_text_renders_only_the_url() -> None:
    assert UrlPart("", "https://example.org").value == "@url{https://example.org}"


@pytest.mark.parametrize("symbol", ["-", ".", "+", ":", ";", ","])
def test_the_word_transformer_builds_every_joiner_from_its_symbol(symbol: str) -> None:
    line = parse_atf_lark(f"1. ku{symbol}nu").lines[0]

    assert isinstance(line, TextLine)
    assert Joiner.of(atf.Joiner(symbol)) in line.content[0].parts
