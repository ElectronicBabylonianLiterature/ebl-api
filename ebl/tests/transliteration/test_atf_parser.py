from typing import List
from lark import Lark
import re

import pytest
from hamcrest.library import starts_with
from ebl.common.domain.period import Period

from ebl.errors import DataError
from ebl.tests.assertions import assert_exception_has_errors
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.at_line import SurfaceAtLine
from ebl.transliteration.domain.dollar_line import ScopeContainer, StateDollarLine
from ebl.transliteration.domain.labels import SurfaceLabel
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.lark_parser import parse_atf_lark
from ebl.transliteration.domain.line import ControlLine, EmptyLine, Line
from ebl.transliteration.domain.stage import ABBREVIATIONS as STAGE_ABBREVIATIONS
from ebl.transliteration.domain.text import Text
from ebl.transliteration.domain.transliteration_error import TransliterationError

DEFAULT_LANGUAGE = Language.AKKADIAN
PARSER_PATH = "../../transliteration/domain/ebl_atf.lark"
LINE_PARSER_PATH = "../../transliteration/domain/ebl_atf_text_line.lark"


@pytest.mark.parametrize(
    "parser,version", [(parse_atf_lark, f"{atf.ATF_PARSER_VERSION}")]
)
def test_parser_version(parser, version):
    assert parser("1. kur").parser_version == version


@pytest.mark.parametrize(
    "line,expected_tokens",
    [
        ("", []),
        ("\n", []),
        (
            "#first\n\n#second",
            [ControlLine("#", "first"), EmptyLine(), ControlLine("#", "second")],
        ),
        (
            "#first\n \n#second",
            [ControlLine("#", "first"), EmptyLine(), ControlLine("#", "second")],
        ),
        ("&K11111", [ControlLine("&", "K11111")]),
        ("@reverse", [SurfaceAtLine(SurfaceLabel([], atf.Surface.REVERSE))]),
        (
            "$ (end of side)",
            [
                StateDollarLine(
                    None,
                    atf.Extent.END_OF,
                    ScopeContainer(atf.Scope.SIDE, ""),
                    None,
                    None,
                )
            ],
        ),
        ("#some notes", [ControlLine("#", "some notes")]),
        ("=: continuation", [ControlLine("=:", " continuation")]),
    ],
)
def test_parse_atf(line: str, expected_tokens: List[Line]) -> None:
    assert parse_atf_lark(line).lines == Text.of_iterable(expected_tokens).lines


@pytest.mark.parametrize(
    "atf,line_numbers",
    [
        ("invalid", [1]),
        ("1. x\nthis is not valid", [2]),
        ("this is not valid\nthis is not valid", [1, 2]),
        ("$ ", [1]),
    ],
)
def test_invalid_atf(atf, line_numbers) -> None:
    with pytest.raises(TransliterationError) as exc_info:  # pyre-ignore[16]
        parse_atf_lark(atf)

    assert_exception_has_errors(exc_info, line_numbers, starts_with("Invalid line"))


@pytest.mark.parametrize("atf", ["1. x\n1. x", "1. x\n@obverse\n1. x\n1. x"])
def test_duplicate_labels(atf) -> None:
    with pytest.raises(DataError, match="Duplicate labels."):  # pyre-ignore[16]
        parse_atf_lark(atf)


def test_stages_periods_equality():
    atf_parser = Lark.open(
        PARSER_PATH,
        rel_to=__file__,
        maybe_placeholders=True,
        start="siglum",
    )

    text_line_parser = Lark.open(
        LINE_PARSER_PATH,
        rel_to=__file__,
        maybe_placeholders=True,
        start="chapter_name",
    )

    atf_parser_periods = set(
        re.findall(
            r"[A-Za-z0-9_]+",
            atf_parser.get_terminal("PERIOD").pattern.value,
        )
    )

    line_parser_stages = set(
        re.findall(
            r"[A-Za-z0-9_]+",
            text_line_parser.get_terminal("STAGE").pattern.value,
        )
    )

    enum_periods = {period.abbreviation for period in Period if period != Period.NONE}

    enum_stages = set(STAGE_ABBREVIATIONS.values())

    assert atf_parser_periods == enum_periods
    assert line_parser_stages - {"SB"} == enum_periods
    assert line_parser_stages == enum_stages
