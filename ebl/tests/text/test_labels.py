import pytest

from ebl.text.atf import Surface, LabelFlag
from ebl.text.labels import parse_label, ColumnLabel, SurfaceLabel


@pytest.mark.parametrize('input,expected', [
    ('o', SurfaceLabel(Surface.OBVERSE)),
    ('r', SurfaceLabel(Surface.REVERSE)),
    ('b.e.', SurfaceLabel(Surface.BOTTOM)),
    ('e.', SurfaceLabel(Surface.EDGE)),
    ('l.e.', SurfaceLabel(Surface.LEFT)),
    ('r.e.', SurfaceLabel(Surface.RIGHT)),
    ('t.e.', SurfaceLabel(Surface.TOP)),
    ("o'", SurfaceLabel(Surface.OBVERSE, LabelFlag.PRIME)),
    ('r?', SurfaceLabel(Surface.REVERSE, LabelFlag.UNCERTAIN)),
    ('b.e.!', SurfaceLabel(Surface.BOTTOM, LabelFlag.CORRECTION)),
    ('e.*', SurfaceLabel(Surface.EDGE, LabelFlag.COLLATION)),
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
    ("i'", ColumnLabel(1, LabelFlag.PRIME)),
    ('ii?', ColumnLabel(2, LabelFlag.UNCERTAIN)),
    ('iii!', ColumnLabel(3, LabelFlag.CORRECTION)),
    ('iv*', ColumnLabel(4, LabelFlag.COLLATION)),
])
def test_parse_label(input, expected):
    assert parse_label(input) == expected
