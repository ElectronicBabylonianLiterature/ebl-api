import pytest  # pyre-ignore

from ebl.transliteration.domain import atf
from ebl.transliteration.domain.at_line import (
    ColumnAtLine,
    CompositeAtLine,
    DiscourseAtLine,
    DivisionAtLine,
    HeadingAtLine,
    ObjectAtLine,
    SurfaceAtLine,
)
from ebl.transliteration.domain.labels import ColumnLabel, ObjectLabel, SurfaceLabel
from ebl.transliteration.domain.lark_parser import parse_atf_lark
from ebl.transliteration.domain.text import Text
from ebl.transliteration.domain.transliteration_error import TransliterationError


@pytest.mark.parametrize(
    "line,expected_tokens",
    [
        ("@composite", [CompositeAtLine(atf.Composite.COMPOSITE, "")]),
        ("@m=locator o 1", [CompositeAtLine(atf.Composite.MILESTONE, "o", 1)]),
        ("@m=locator o", [CompositeAtLine(atf.Composite.MILESTONE, "o")]),
        ("@div part 1", [CompositeAtLine(atf.Composite.DIV, "part", 1)]),
        ("@end part", [CompositeAtLine(atf.Composite.END, "part")]),
        ("@m=division paragraph ", [DivisionAtLine("paragraph")]),
        ("@m=division paragraph 1", [DivisionAtLine("paragraph", 1)]),
        ("@date", [DiscourseAtLine(atf.Discourse.DATE)]),
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
        ("@edge", [SurfaceAtLine(SurfaceLabel([], atf.Surface.EDGE, ""))]),
        ("@edge a", [SurfaceAtLine(SurfaceLabel([], atf.Surface.EDGE, "a"))]),
        (
            "@surface stone",
            [SurfaceAtLine(SurfaceLabel([], atf.Surface.SURFACE, "stone"))],
        ),
        (
            "@prism!",
            [ObjectAtLine(ObjectLabel([atf.Status.CORRECTION], atf.Object.PRISM))],
        ),
        ("@prism", [ObjectAtLine(ObjectLabel([], atf.Object.PRISM))]),
        ("@object stone", [ObjectAtLine(ObjectLabel([], atf.Object.OBJECT, "stone"))]),
        ("@fragment 1", [ObjectAtLine(ObjectLabel([], atf.Object.FRAGMENT, "1"))]),
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
def test_parse_atf_at_line(line, expected_tokens):
    assert parse_atf_lark(line).lines == Text.of_iterable(expected_tokens).lines


def test_parse_atf_at_line_duplicate_status_error():
    with pytest.raises(TransliterationError) as exc_info:
        parse_atf_lark("@column 1!!")
    assert exc_info.value.errors == [
        {"description": "Duplicate Status", "lineNumber": 1}
    ]
