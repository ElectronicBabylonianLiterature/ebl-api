from typing import List, Tuple

import pytest  # pyre-ignore[21]

from ebl.transliteration.domain.atf import Status, Surface, Object
from ebl.transliteration.domain.labels import (
    parse_label,
    ColumnLabel,
    Label,
    LabelVisitor,
    SurfaceLabel,
    ObjectLabel,
)

LABELS: List[Tuple[str, str, str, Label]] = [
    ("o", "", "@obverse", SurfaceLabel(tuple(), Surface.OBVERSE)),
    ("r", "", "@reverse", SurfaceLabel(tuple(), Surface.REVERSE)),
    ("b.e.", "", "@bottom", SurfaceLabel(tuple(), Surface.BOTTOM)),
    ("e.", "", "@edge", SurfaceLabel(tuple(), Surface.EDGE)),
    ("l.e.", "", "@left", SurfaceLabel(tuple(), Surface.LEFT)),
    ("r.e.", "", "@right", SurfaceLabel(tuple(), Surface.RIGHT)),
    ("t.e.", "", "@top", SurfaceLabel(tuple(), Surface.TOP)),
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
]


UNPARSEABLE_LABELS: List[Tuple[str, str, str, Label]] = [
    ("a", "", "@edge a", SurfaceLabel(tuple(), Surface.EDGE, "a")),
    ("side a", "", "@surface side a", SurfaceLabel(tuple(), Surface.SURFACE, "side a")),
    ("a", "", "@face a", SurfaceLabel(tuple(), Surface.FACE, "a")),
    ("bulla", "", "@bulla", ObjectLabel(tuple(), Object.BULLA, "")),
    ("envelope", "", "@envelope", ObjectLabel(tuple(), Object.ENVELOPE, "")),
    ("a", "", "@fragment a", ObjectLabel(tuple(), Object.FRAGMENT, "a")),
    (
        "Stone wig",
        "",
        "@object Stone wig",
        ObjectLabel(tuple(), Object.OBJECT, "Stone wig"),
    ),
    ("prism", "", "@prism", ObjectLabel(tuple(), Object.PRISM, "")),
    ("tablet", "", "@tablet", ObjectLabel(tuple(), Object.TABLET, "")),
]


@pytest.mark.parametrize("label,status,_,expected", LABELS)  # pyre-ignore[56]
def test_parse_label(label, status, _, expected) -> None:
    assert parse_label(f"{label}{status}") == expected


# pyre-ignore[56]
@pytest.mark.parametrize("label,status,_,model", LABELS + UNPARSEABLE_LABELS)
def test_abbreviation(label, status, _, model) -> None:
    assert model.abbreviation == label


# pyre-ignore[56]
@pytest.mark.parametrize("label,status,_,model", LABELS + UNPARSEABLE_LABELS)
def test_label_to_value(label, status, _, model) -> None:
    assert model.to_value() == f"{label}{status}"


# pyre-ignore[56]
@pytest.mark.parametrize("_, status,atf,model", LABELS + UNPARSEABLE_LABELS)
def test_label_to_atf(_, status, atf, model) -> None:
    assert model.to_atf() == f"{atf}{status}"


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
