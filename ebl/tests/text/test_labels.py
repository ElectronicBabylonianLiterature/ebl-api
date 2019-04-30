import pytest

from ebl.text.atf import Surface, Status
from ebl.text.labels import Label, ColumnLabel, SurfaceLabel

LABELS = [
    ('o', SurfaceLabel(tuple(), Surface.OBVERSE)),
    ('r', SurfaceLabel(tuple(), Surface.REVERSE)),
    ('b.e.', SurfaceLabel(tuple(), Surface.BOTTOM)),
    ('e.', SurfaceLabel(tuple(), Surface.EDGE)),
    ('l.e.', SurfaceLabel(tuple(), Surface.LEFT)),
    ('r.e.', SurfaceLabel(tuple(), Surface.RIGHT)),
    ('t.e.', SurfaceLabel(tuple(), Surface.TOP)),
    ("o'", SurfaceLabel((Status.PRIME, ), Surface.OBVERSE)),
    ('r?', SurfaceLabel((Status.UNCERTAIN, ), Surface.REVERSE)),
    ('b.e.!', SurfaceLabel((Status.CORRECTION, ), Surface.BOTTOM)),
    ('e.*', SurfaceLabel((Status.COLLATION, ), Surface.EDGE)),
    ('l.e.*!',
     SurfaceLabel((Status.COLLATION, Status.CORRECTION), Surface.LEFT)),
    ('i', ColumnLabel(tuple(), 1)),
    ('ii', ColumnLabel(tuple(), 2)),
    ('iii', ColumnLabel(tuple(), 3)),
    ('iv', ColumnLabel(tuple(), 4)),
    ('v', ColumnLabel(tuple(), 5)),
    ('vi', ColumnLabel(tuple(), 6)),
    ('vii', ColumnLabel(tuple(), 7)),
    ('viii', ColumnLabel(tuple(), 8)),
    ('ix', ColumnLabel(tuple(), 9)),
    ('x', ColumnLabel(tuple(), 10)),
    ("i'", ColumnLabel((Status.PRIME, ), 1)),
    ('ii?', ColumnLabel((Status.UNCERTAIN, ), 2)),
    ('iii!', ColumnLabel((Status.CORRECTION, ), 3)),
    ('iv*', ColumnLabel((Status.COLLATION, ), 4)),
    ("v'?", ColumnLabel((Status.PRIME, Status.UNCERTAIN), 5)),
]


@pytest.mark.parametrize('label,expected', LABELS)
def test_parse_label(label, expected):
    assert Label.parse(label) == expected


@pytest.mark.parametrize('label,model', LABELS)
def test_label_to_value(label, model):
    assert model.to_value() == label
