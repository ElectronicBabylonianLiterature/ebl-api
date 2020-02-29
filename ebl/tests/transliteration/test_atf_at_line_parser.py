import pytest

from ebl.transliteration.domain import atf
from ebl.transliteration.domain.at_line import (
    HeadingAtLine,
    ColumnAtLine,
    DiscourseAtLine,
    SurfaceAtLine,
    ObjectAtLine,
)
from ebl.transliteration.domain.labels import ColumnLabel, SurfaceLabel
from ebl.transliteration.domain.lark_parser import parse_atf_lark
from ebl.transliteration.domain.text import Text


@pytest.mark.parametrize("parser", [parse_atf_lark])
@pytest.mark.parametrize(
    "line,expected_tokens",
    [
        (
            "@reverse!*",
            [
                SurfaceAtLine(
                    SurfaceLabel(
                        [atf.Status.CORRECTION, atf.Status.COLLATION],
                        atf.Surface.REVERSE,
                    )
                )
            ],
        ),
        (
            "@reverse!",
            [SurfaceAtLine(SurfaceLabel([atf.Status.CORRECTION], atf.Surface.REVERSE))],
        ),
        ("@reverse", [SurfaceAtLine(SurfaceLabel([], atf.Surface.REVERSE))]),
        (
            "@surface stone",
            [SurfaceAtLine(SurfaceLabel([], atf.Surface.SURFACE, "stone"))],
        ),
        ("@prism!", [ObjectAtLine([atf.Status.CORRECTION], atf.Object.PRISM)]),
        ("@prism", [ObjectAtLine([], atf.Object.PRISM)]),
        ("@object stone", [ObjectAtLine([], atf.Object.OBJECT, "stone")]),
        ("@edge a", [SurfaceAtLine(SurfaceLabel([], atf.Surface.EDGE, "a"))]),
        ("@face a", [SurfaceAtLine(SurfaceLabel([], atf.Surface.FACE, "a"))]),
        ("@h1", [HeadingAtLine(1)]),
        ("@column 1", [ColumnAtLine(ColumnLabel.from_int(1))]),
        (
            "@column 1!",
            [ColumnAtLine(ColumnLabel.from_int(1, (atf.Status.CORRECTION,)))],
        ),
        (
            "@column 1!*",
            [
                ColumnAtLine(
                    ColumnLabel.from_int(
                        1, (atf.Status.CORRECTION, atf.Status.COLLATION)
                    )
                )
            ],
        ),
        ("@date", [DiscourseAtLine(atf.Discourse.DATE)]),
    ],
)
def test_parse_atf_at_line(parser, line, expected_tokens):
    assert parser(line).lines == Text.of_iterable(expected_tokens).lines
