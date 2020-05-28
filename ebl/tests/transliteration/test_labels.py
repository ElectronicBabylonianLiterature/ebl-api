import pytest  # pyre-ignore

from ebl.transliteration.domain.atf import Status, Surface
from ebl.transliteration.domain.labels import (
    parse_label,
    ColumnLabel,
    Label,
    LabelVisitor,
    LineNumberLabel,
    SurfaceLabel,
)

LABELS = [
    ("o", "", "@obverse", SurfaceLabel(tuple(), Surface.OBVERSE)),
    ("r", "", "@reverse", SurfaceLabel(tuple(), Surface.REVERSE)),
    ("b.e.", "", "@bottom", SurfaceLabel(tuple(), Surface.BOTTOM)),
    ("e.", "", "@edge", SurfaceLabel(tuple(), Surface.EDGE)),
    ("l.e.", "", "@left", SurfaceLabel(tuple(), Surface.LEFT)),
    ("r.e.", "", "@right", SurfaceLabel(tuple(), Surface.RIGHT)),
    ("t.e.", "","@top", SurfaceLabel(tuple(), Surface.TOP)),
    ("o", "'", "@obverse", SurfaceLabel((Status.PRIME,), Surface.OBVERSE)),
    ("r", "?", "@reverse", SurfaceLabel((Status.UNCERTAIN,), Surface.REVERSE)),
    ("b.e.", "!", "@bottom", SurfaceLabel((Status.CORRECTION,), Surface.BOTTOM)),
    ("e.", "*", "@edge", SurfaceLabel((Status.COLLATION,), Surface.EDGE)),
    (
        "l.e.",
        "*!",
        "@left",
        SurfaceLabel((Status.COLLATION, Status.CORRECTION), Surface.LEFT),
    ),
    ("i", "", "@column 1", ColumnLabel(tuple(), 1)),
    ("ii", "", "@column 2", ColumnLabel(tuple(), 2)),
    ("iii", "", "@column 3", ColumnLabel(tuple(), 3)),
    ("iv", "", "@column 4", ColumnLabel(tuple(), 4)),
    ("v", "", "@column 5", ColumnLabel(tuple(), 5)),
    ("vi", "", "@column 6", ColumnLabel(tuple(), 6)),
    ("vii", "", "@column 7", ColumnLabel(tuple(), 7)),
    ("viii", "", "@column 8", ColumnLabel(tuple(), 8)),
    ("ix", "", "@column 9", ColumnLabel(tuple(), 9)),
    ("x", "", "@column 10", ColumnLabel(tuple(), 10)),
    ("i", "'", "@column 1", ColumnLabel((Status.PRIME,), 1)),
    ("ii", "?", "@column 2", ColumnLabel((Status.UNCERTAIN,), 2)),
    ("iii", "!", "@column 3", ColumnLabel((Status.CORRECTION,), 3)),
    ("iv", "*", "@column 4", ColumnLabel((Status.COLLATION,), 4)),
    ("v", "'?", "@column 5", ColumnLabel((Status.PRIME, Status.UNCERTAIN), 5)),
    ("1", "", "1.", LineNumberLabel("1")),
    ("a+1", "", "a+1.", LineNumberLabel("a+1")),
    ("2'", "", "2'.", LineNumberLabel("2'")),
]


@pytest.mark.parametrize("label,status,_,expected", LABELS)
def test_parse_label(label, status, _, expected) -> None:
    assert parse_label(f"{label}{status}") == expected


@pytest.mark.parametrize("label,status,_,model", LABELS)
def test_abbreviation(label, status, _, model) -> None:
    assert model.abbreviation == label


@pytest.mark.parametrize("label,status,_,model", LABELS)
def test_label_to_value(label, status, _, model) -> None:
    assert model.to_value() == f"{label}{status}"


@pytest.mark.parametrize("_, status,atf,model", LABELS)
def test_label_to_atf(_, status, atf, model) -> None:
    assert model.to_atf() == f"{atf}{status}"


@pytest.mark.parametrize("number", ["", " ", " 1", "1 ", "1 2", "\t"])
def test_not_atf_line_number_is_invalid(number) -> None:
    with pytest.raises(ValueError):
        LineNumberLabel(number)


def test_duplicate_status_is_invalid() -> None:
    class TestLabel(Label):
        @property
        def _atf(self) -> str:
            return ""

        @property
        def abbreviation(self) -> str:
            return ""

        def accept(self, visitor: LabelVisitor) -> LabelVisitor:
            return visitor

    with pytest.raises(ValueError):
        TestLabel((Status.PRIME, Status.PRIME))
