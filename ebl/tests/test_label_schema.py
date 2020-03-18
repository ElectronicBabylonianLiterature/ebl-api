from ebl.transliteration.application.line_schemas import (
    ColumnLabelSchema,
    SurfaceLabelSchema,
)
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.labels import ColumnLabel, SurfaceLabel


def test_load_and_dump_column_label_schema():
    column_label = ColumnLabel([], 1)
    dump = ColumnLabelSchema().dump(column_label)
    assert dump == {"column": 1, "status": []}
    assert ColumnLabelSchema().load(dump) == column_label


def test_load_and_dump_surface_label_schema():
    surface_label = SurfaceLabel(
        [atf.Status.CORRECTION], atf.Surface.SURFACE, "stone wig"
    )
    dump = SurfaceLabelSchema().dump(surface_label)
    assert dump == {"status": ["CORRECTION"], "surface": "SURFACE", "text": "stone wig"}
    assert SurfaceLabelSchema().load(dump) == surface_label
