from typing import List

import pytest  # pyre-ignore[21]
from hamcrest.library import starts_with  # pyre-ignore[21]

from ebl.errors import DataError
from ebl.tests.assertions import assert_exception_has_errors
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.at_line import SurfaceAtLine
from ebl.transliteration.domain.dollar_line import ScopeContainer, StateDollarLine
from ebl.transliteration.domain.labels import SurfaceLabel
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.lark_parser import parse_atf_lark
from ebl.transliteration.domain.line import ControlLine, EmptyLine, Line
from ebl.transliteration.domain.text import Text
from ebl.transliteration.domain.transliteration_error import TransliterationError

DEFAULT_LANGUAGE = Language.AKKADIAN


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
    with pytest.raises(TransliterationError) as exc_info:
        parse_atf_lark(atf)

    assert_exception_has_errors(exc_info, line_numbers, starts_with("Invalid line"))


@pytest.mark.parametrize(
    "atf,line_numbers", [("1. x\n1. x", [2]), ("1. x\n@obverse\n1. x\n1. x", [4])]
)
def test_duplicate_labels(atf, line_numbers) -> None:
    with pytest.raises(DataError, match="Duplicate labels."):
        parse_atf_lark(atf)
