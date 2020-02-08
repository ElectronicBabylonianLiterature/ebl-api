import pytest

from ebl.transliteration.domain import atf
from ebl.transliteration.domain.lark_parser import parse_atf_lark
from ebl.transliteration.domain.line import (
    LooseDollarLine,
    ImageDollarLine,
    RulingDollarLine,
    StrictDollarLine,
    ScopeContainer,
)
from ebl.transliteration.domain.text import Text


@pytest.mark.parametrize("parser", [parse_atf_lark])
@pytest.mark.parametrize(
    "line,expected_tokens",
    [
        ("$ (end of side)", [LooseDollarLine("end of side")]),
        ("$ (image 1a = great)", [ImageDollarLine("1", "a", "great")]),
        (
            "$ (image 1 = numbered diagram of triangle)",
            [ImageDollarLine("1", None, "numbered diagram of triangle")],
        ),
        ("$ single ruling", [RulingDollarLine(atf.Ruling.SINGLE)]),
        ("$ double ruling", [RulingDollarLine(atf.Ruling.DOUBLE)]),
        ("$ triple ruling", [RulingDollarLine(atf.Ruling.TRIPLE)]),
    ],
)
def test_parse_atf_dollar_line(parser, line, expected_tokens):
    assert parser(line).lines == Text.of_iterable(expected_tokens).lines


@pytest.mark.parametrize("parser", [parse_atf_lark])
@pytest.mark.parametrize(
    "line,expected_tokens",
    [
        (
            "$ at least 1 obverse missing",
            [
                StrictDollarLine(
                    atf.Qualification.AT_LEAST,
                    1,
                    ScopeContainer(atf.Surface.OBVERSE, ""),
                    atf.State.MISSING,
                    None,
                )
            ],
        ),
        (
            "$ 2 lines",
            [StrictDollarLine(None, 2, ScopeContainer(atf.Scope.LINES), None, None,)],
        ),
        (
            "$ at most 1-3 object stone blank ?",
            [
                StrictDollarLine(
                    atf.Qualification.AT_MOST,
                    (1, 3),
                    ScopeContainer(atf.Object.OBJECT, "stone"),
                    atf.State.BLANK,
                    atf.Status.UNCERTAIN,
                )
            ],
        ),
        (
            "$ at most 1-3 obverse",
            [
                StrictDollarLine(
                    atf.Qualification.AT_MOST,
                    (1, 3),
                    ScopeContainer(atf.Surface.OBVERSE),
                    None,
                    None,
                )
            ],
        ),
        (
            "$ 1-3 obverse",
            [
                StrictDollarLine(
                    None, (1, 3), ScopeContainer(atf.Surface.OBVERSE), None, None,
                )
            ],
        ),
        (
            "$ 1 - 3 obverse",
            [
                StrictDollarLine(
                    None, (1, 3), ScopeContainer(atf.Surface.OBVERSE), None, None,
                )
            ],
        ),
        (
            "$ 1 obverse",
            [
                StrictDollarLine(
                    None, 1, ScopeContainer(atf.Surface.OBVERSE), None, None,
                )
            ],
        ),
        (
            "$ several obverse",
            [
                StrictDollarLine(
                    None,
                    atf.Extent.SEVERAL,
                    ScopeContainer(atf.Surface.OBVERSE),
                    None,
                    None,
                )
            ],
        ),
        (
            "$ several obverse",
            [
                StrictDollarLine(
                    None,
                    atf.Extent.SEVERAL,
                    ScopeContainer(atf.Surface.OBVERSE),
                    None,
                    None,
                )
            ],
        ),
        (
            "$ several obverse",
            [
                StrictDollarLine(
                    None,
                    atf.Extent.SEVERAL,
                    ScopeContainer(atf.Surface.OBVERSE),
                    None,
                    None,
                )
            ],
        ),
        (
            "$ several obverse blank *",
            [
                StrictDollarLine(
                    None,
                    atf.Extent.SEVERAL,
                    ScopeContainer(atf.Surface.OBVERSE),
                    atf.State.BLANK,
                    atf.Status.COLLATION,
                )
            ],
        ),
        (
            "$ several surface stone blank *",
            [
                StrictDollarLine(
                    None,
                    atf.Extent.SEVERAL,
                    ScopeContainer(atf.Surface.SURFACE, "stone"),
                    atf.State.BLANK,
                    atf.Status.COLLATION,
                )
            ],
        ),
        (
            "$ several object stone blank *",
            [
                StrictDollarLine(
                    None,
                    atf.Extent.SEVERAL,
                    ScopeContainer(atf.Object.OBJECT, "stone"),
                    atf.State.BLANK,
                    atf.Status.COLLATION,
                )
            ],
        ),
        (
            "$ several tablet blank *",
            [
                StrictDollarLine(
                    None,
                    atf.Extent.SEVERAL,
                    ScopeContainer(atf.Object.TABLET),
                    atf.State.BLANK,
                    atf.Status.COLLATION,
                )
            ],
        ),
    ],
)
def test_parse_atf_strict_dollar_line(parser, line, expected_tokens):
    assert parser(line).lines == Text.of_iterable(expected_tokens).lines


@pytest.mark.parametrize("parser", [parse_atf_lark])
@pytest.mark.parametrize(
    "line,expected_tokens",
    [
        (
            "$ (at least 1 obverse missing)",
            [
                StrictDollarLine(
                    atf.Qualification.AT_LEAST,
                    1,
                    ScopeContainer(atf.Surface.OBVERSE, ""),
                    atf.State.MISSING,
                    None,
                )
            ],
        ),
        (
            "$ (at least 1 obverse issing)",
            [LooseDollarLine("at least 1 obverse issing")],
        ),
    ],
)
def test_parse_atf_loose_to_strict_dollar_line(parser, line, expected_tokens):
    assert parser(line).lines == Text.of_iterable(expected_tokens).lines
