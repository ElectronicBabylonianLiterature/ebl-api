import pytest

from ebl.transliteration.domain import atf
from ebl.transliteration.domain.labels import ColumnLabel, SurfaceLabel, ObjectLabel
from ebl.transliteration.domain.line_label import LineLabel
from ebl.transliteration.domain.line_number import LineNumber, LineNumberRange


@pytest.mark.parametrize(
    "line_label, expected",
    [
        (
            LineLabel(
                ColumnLabel.from_int(1),
                SurfaceLabel([], atf.Surface.SURFACE, "Stone wig"),
                ObjectLabel([], atf.Object.OBJECT, "Stone wig"),
                LineNumber(2),
            ),
            "2. i Stone wig Stone wig",
        ),
        (
            LineLabel(
                None, None, None, LineNumberRange(LineNumber(1, True), LineNumber(3))
            ),
            "1'-3.",
        ),
    ],
)
def test_line_label(line_label, expected):
    assert line_label.abbreviation == expected


@pytest.mark.parametrize(
    "line_label, line_number, expected",
    [
        (
            LineLabel(
                ColumnLabel.from_int(1),
                SurfaceLabel([], atf.Surface.SURFACE, "Stone wig"),
                ObjectLabel([], atf.Object.OBJECT, "Stone wig"),
                LineNumber(2),
            ),
            2,
            True,
        ),
        (
            LineLabel(
                ColumnLabel.from_int(1),
                SurfaceLabel([], atf.Surface.SURFACE, "Stone wig"),
                ObjectLabel([], atf.Object.OBJECT, "Stone wig"),
                LineNumber(2),
            ),
            1,
            False,
        ),
        (
            LineLabel(
                ColumnLabel.from_int(1),
                SurfaceLabel([], atf.Surface.SURFACE, "Stone wig"),
                ObjectLabel([], atf.Object.OBJECT, "Stone wig"),
                LineNumberRange(LineNumber(1, True), LineNumber(3)),
            ),
            2,
            True,
        ),
        (
            LineLabel(
                ColumnLabel.from_int(1),
                SurfaceLabel([], atf.Surface.SURFACE, "Stone wig"),
                ObjectLabel([], atf.Object.OBJECT, "Stone wig"),
                LineNumberRange(LineNumber(1, True), LineNumber(3)),
            ),
            4,
            False,
        ),
    ],
)
def test_line_label_match_line_number(line_label, line_number, expected):
    assert line_label.matches_line_number(line_number) == expected
