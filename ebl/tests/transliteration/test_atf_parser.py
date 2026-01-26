from typing import List
from lark import Lark, UnexpectedCharacters
import re

import pytest
from hamcrest.library import starts_with
from ebl.common.domain.period import Period
from ebl.common.domain.provenance import Provenance

from ebl.transliteration.domain.transliteration_error import DuplicateLabelError
from ebl.tests.assertions import assert_exception_has_errors
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.at_line import SurfaceAtLine
from ebl.transliteration.domain.dollar_line import ScopeContainer, StateDollarLine
from ebl.transliteration.domain.labels import SurfaceLabel
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.atf_parsers.lark_parser import parse_atf_lark
from ebl.transliteration.domain.line import ControlLine, Line
from ebl.common.domain.stage import Stage
from ebl.transliteration.domain.text import Text
from ebl.transliteration.domain.transliteration_error import TransliterationError

DEFAULT_LANGUAGE = Language.AKKADIAN
MANUSCRIPT_LINE_PARSER_PATH = (
    "../../transliteration/domain/atf_parsers/lark_parser/ebl_atf_manuscript_line.lark"
)
PARALLEL_LINE_PARSER_PATH = (
    "../../transliteration/domain/atf_parsers/lark_parser/ebl_atf_parallel_line.lark"
)


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
        ("#first\n\n#second", [1, 3]),
    ],
)
def test_invalid_atf(atf, line_numbers) -> None:
    with pytest.raises(TransliterationError) as exc_info:  # pyre-ignore[16]
        parse_atf_lark(atf)

    assert_exception_has_errors(exc_info, line_numbers, starts_with("Invalid line"))


@pytest.mark.parametrize("atf", ["1. x\n1. x", "1. x\n@obverse\n1. x\n1. x"])
def test_duplicate_labels(atf):
    with pytest.raises(DuplicateLabelError, match="Duplicate labels"):
        parse_atf_lark(atf)


@pytest.fixture
def siglum_parser():
    return Lark.open(
        MANUSCRIPT_LINE_PARSER_PATH,
        rel_to=__file__,
        maybe_placeholders=True,
        start="siglum",
    )


def test_stages_periods_equality(siglum_parser):
    text_line_parser = Lark.open(
        PARALLEL_LINE_PARSER_PATH,
        rel_to=__file__,
        maybe_placeholders=True,
        start="chapter_name",
    )

    atf_parser_periods = set(
        re.findall(
            r"[A-Za-z0-9_]+",
            siglum_parser.get_terminal("PERIOD").pattern.value,
        )
    )

    line_parser_stages = set(
        re.findall(
            r"[A-Za-z0-9_]+",
            text_line_parser.get_terminal("STAGE").pattern.value,
        )
    )

    enum_periods = {period.abbreviation for period in Period if period != Period.NONE}

    enum_stages = {stage.abbreviation for stage in Stage}

    assert atf_parser_periods == enum_periods
    assert line_parser_stages - {"SB"} == enum_periods
    assert line_parser_stages == enum_stages


@pytest.mark.parametrize("provenance", Provenance)
def test_provenances_coverage(siglum_parser, provenance):
    abbreviation = provenance.abbreviation
    mock_siglum = f"{abbreviation}NA"
    try:
        siglum_parser.parse(mock_siglum)
    except UnexpectedCharacters as e:
        raise ValueError(
            f"Cannot parse {provenance.long_name!r}: "
            f"Is {abbreviation!r} in PROVENANCES in ebl_atf.lark?"
            "If yes, make sure it occurs *above* any entries with the same prefix,"
            f"e.g., {abbreviation[:-1]!r}"
        ) from e
