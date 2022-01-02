from ebl.transliteration.domain import atf
from ebl.transliteration.domain.labels import ColumnLabel, SurfaceLabel, ObjectLabel
from ebl.transliteration.domain.line_label import LineLabel
from ebl.transliteration.domain.line_number import LineNumber


def test_line_label():
    line_label = LineLabel(
        ColumnLabel.from_int(1),
        SurfaceLabel([], atf.Surface.SURFACE, "Stone wig"),
        ObjectLabel([], atf.Object.OBJECT, "Stone wig"),
        LineNumber(2),
    )
    assert line_label.abbreviation == "2. i Stone wig Stone wig"


def test_line_label_empty_labels():
    line_label = LineLabel(None, None, None, LineNumber(2, True))
    assert line_label.abbreviation == "2'."
