import pytest

from ebl.text.atf import Surface, Status
from ebl.text.labels import Label, ColumnLabel, SurfaceLabel

LABELS = [
    ('o', SurfaceLabel(Status.NONE, Surface.OBVERSE)),
    ('r', SurfaceLabel(Status.NONE, Surface.REVERSE)),
    ('b.e.', SurfaceLabel(Status.NONE, Surface.BOTTOM)),
    ('e.', SurfaceLabel(Status.NONE, Surface.EDGE)),
    ('l.e.', SurfaceLabel(Status.NONE, Surface.LEFT)),
    ('r.e.', SurfaceLabel(Status.NONE, Surface.RIGHT)),
    ('t.e.', SurfaceLabel(Status.NONE, Surface.TOP)),
    ("o'", SurfaceLabel(Status.PRIME, Surface.OBVERSE)),
    ('r?', SurfaceLabel(Status.UNCERTAIN, Surface.REVERSE)),
    ('b.e.!', SurfaceLabel(Status.CORRECTION, Surface.BOTTOM)),
    ('e.*', SurfaceLabel(Status.COLLATION, Surface.EDGE)),
    ('i', ColumnLabel(Status.NONE, 1)),
    ('ii', ColumnLabel(Status.NONE, 2)),
    ('iii', ColumnLabel(Status.NONE, 3)),
    ('iv', ColumnLabel(Status.NONE, 4)),
    ('v', ColumnLabel(Status.NONE, 5)),
    ('vi', ColumnLabel(Status.NONE, 6)),
    ('vii', ColumnLabel(Status.NONE, 7)),
    ('viii', ColumnLabel(Status.NONE, 8)),
    ('ix', ColumnLabel(Status.NONE, 9)),
    ('x', ColumnLabel(Status.NONE, 10)),
    ("i'", ColumnLabel(Status.PRIME, 1)),
    ('ii?', ColumnLabel(Status.UNCERTAIN, 2)),
    ('iii!', ColumnLabel(Status.CORRECTION, 3)),
    ('iv*', ColumnLabel(Status.COLLATION, 4))
]


@pytest.mark.parametrize('label,expected', LABELS)
def test_parse_label(label, expected):
    assert Label.parse(label) == expected


@pytest.mark.parametrize('label,model', LABELS)
def test_label_to_value(label, model):
    assert model.to_value() == label
