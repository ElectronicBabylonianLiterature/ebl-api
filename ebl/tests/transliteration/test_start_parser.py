import copy
from typing import cast

import pytest
from lark.lark import LarkOptions

from lark.exceptions import ParseError

from ebl.transliteration.domain.line import Line

from ebl.transliteration.domain.atf_parsers.lark_parser import (
    LINE_PARSER,
    WORD_PARSER,
    _StartParser,
    validate_line,
)


def test_parse_uses_default_start() -> None:
    tree = WORD_PARSER.parse("kur")

    assert tree == LINE_PARSER.parse("kur", start="any_word")


def _attribute(target: object, name: str) -> object:
    return getattr(target, name)


def test_options_are_the_wrapped_parsers_options() -> None:
    assert isinstance(WORD_PARSER.options, LarkOptions)
    assert WORD_PARSER.options is LINE_PARSER.options


def test_the_wrapper_does_not_delegate_unknown_attributes() -> None:
    with pytest.raises(AttributeError):
        _attribute(WORD_PARSER, "does_not_exist")


def test_an_uninitialised_wrapper_raises_attribute_error() -> None:
    uninitialised = _StartParser.__new__(_StartParser)

    with pytest.raises(AttributeError):
        _attribute(uninitialised, "parse_interactive")


def test_wrapper_is_copyable() -> None:
    copied = copy.deepcopy(WORD_PARSER)

    assert copied.parse("kur") == WORD_PARSER.parse("kur")


def test_validate_line_rejects_untransformed_tree():
    with pytest.raises(ParseError):
        validate_line(cast(Line, LINE_PARSER.parse("kur", start="any_word")))
