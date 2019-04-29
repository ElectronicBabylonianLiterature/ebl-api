import pytest

from ebl.text.atf import Surface, Status
from ebl.text.labels import parse_label, ColumnLabel, SurfaceLabel


@pytest.mark.parametrize('input,expected', [
    ('o', SurfaceLabel(Surface.OBVERSE)),
    ('r', SurfaceLabel(Surface.REVERSE)),
    ('b.e.', SurfaceLabel(Surface.BOTTOM)),
    ('e.', SurfaceLabel(Surface.EDGE)),
    ('l.e.', SurfaceLabel(Surface.LEFT)),
    ('r.e.', SurfaceLabel(Surface.RIGHT)),
    ('t.e.', SurfaceLabel(Surface.TOP)),
    ("o'", SurfaceLabel(Surface.OBVERSE, Status.PRIME)),
    ('r?', SurfaceLabel(Surface.REVERSE, Status.UNCERTAIN)),
    ('b.e.!', SurfaceLabel(Surface.BOTTOM, Status.CORRECTION)),
    ('e.*', SurfaceLabel(Surface.EDGE, Status.COLLATION)),
    ('i', ColumnLabel(1)),
    ('ii', ColumnLabel(2)),
    ('iii', ColumnLabel(3)),
    ('iv', ColumnLabel(4)),
    ('v', ColumnLabel(5)),
    ('vi', ColumnLabel(6)),
    ('vii', ColumnLabel(7)),
    ('viii', ColumnLabel(8)),
    ('ix', ColumnLabel(9)),
    ('x', ColumnLabel(10)),
    ("i'", ColumnLabel(1, Status.PRIME)),
    ('ii?', ColumnLabel(2, Status.UNCERTAIN)),
    ('iii!', ColumnLabel(3, Status.CORRECTION)),
    ('iv*', ColumnLabel(4, Status.COLLATION)),
])
def test_parse_label(input, expected):
    assert parse_label(input) == expected
