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
                None,
            ),
            "i Stone wig Stone wig 2",
        ),
        (
            LineLabel(
                None,
                None,
                None,
                LineNumberRange(LineNumber(1, True), LineNumber(3)),
                None,
            ),
            "1'-3",
        ),
    ],
)
def test_format_line_label(line_label, expected, annotations_service):
    assert line_label.formatted_label == expected
