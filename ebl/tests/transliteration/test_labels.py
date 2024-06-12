from typing import List, Tuple

import pytest

from ebl.transliteration.domain.atf import Status, Surface, Object
from ebl.transliteration.domain.labels import (
    parse_labels,
    ColumnLabel,
    Label,
    LabelVisitor,
    SurfaceLabel,
    ObjectLabel,
)
from ebl.transliteration.domain.atf_parsers.lark_parser_errors import PARSE_ERRORS

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


UNPARSABLE_LABELS: List[Tuple[str, str, str, Label]] = [
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


@pytest.mark.parametrize("label,status,_,expected", LABELS)
def test_parse_labels(label, status, _, expected) -> None:
    assert parse_labels(f"{label}{status}") == (expected,)


def test_parse_labels_multiple() -> None:
    labels = (SurfaceLabel.from_label(Surface.OBVERSE), ColumnLabel.from_int(3))
    assert parse_labels(" ".join(label.to_value() for label in labels)) == labels


def test_parse_labels_empty() -> None:
    assert parse_labels("") == tuple()


@pytest.mark.parametrize("labels", ["o r", "i iii", "i o"])
def test_parse_labels_invalud(labels) -> None:
    with pytest.raises(PARSE_ERRORS):  # pyre-ignore[16]
        parse_labels(labels)


@pytest.mark.parametrize("label,status,_,model", LABELS + UNPARSABLE_LABELS)
def test_abbreviation(label, status, _, model) -> None:
    assert model.abbreviation == label


@pytest.mark.parametrize("label,status,_,model", LABELS + UNPARSABLE_LABELS)
def test_label_to_value(label, status, _, model) -> None:
    assert model.to_value() == f"{label}{status}"


@pytest.mark.parametrize("_, status,atf,model", LABELS + UNPARSABLE_LABELS)
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

    with pytest.raises(ValueError):  # pyre-ignore[16]
        TestLabel((Status.PRIME, Status.PRIME))
