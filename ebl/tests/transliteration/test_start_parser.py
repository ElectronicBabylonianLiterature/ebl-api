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


def test_getattr_delegates_to_wrapped_parser() -> None:
    assert isinstance(WORD_PARSER.options, LarkOptions)
    assert WORD_PARSER.options is LINE_PARSER.options


def test_getattr_raises_for_missing_attribute() -> None:
    missing_attribute = "does_not_exist"

    with pytest.raises(AttributeError):
        getattr(WORD_PARSER, missing_attribute)


def test_getattr_without_initialised_parser_raises_attribute_error() -> None:
    uninitialised = _StartParser.__new__(_StartParser)
    delegated_attribute = "parse_interactive"

    with pytest.raises(AttributeError):
        getattr(uninitialised, delegated_attribute)


def test_wrapper_is_copyable() -> None:
    copied = copy.deepcopy(WORD_PARSER)

    assert copied.parse("kur") == WORD_PARSER.parse("kur")


def test_validate_line_rejects_untransformed_tree():
    with pytest.raises(ParseError):
        validate_line(cast(Line, LINE_PARSER.parse("kur", start="any_word")))
