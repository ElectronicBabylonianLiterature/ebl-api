from ebl.transliteration.application.at_line_schemas import (
    ColumnLabelSchema,
    ObjectLabelSchema,
    SurfaceLabelSchema,
)
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.labels import ColumnLabel, ObjectLabel, SurfaceLabel


def test_load_and_dump_column_label_schema():
    column_label = ColumnLabel([], 1)
    dump = ColumnLabelSchema().dump(column_label)
    assert dump == {"column": 1, "status": [], "abbreviation": "i"}
    assert ColumnLabelSchema().load(dump) == column_label


def test_load_and_dump_surface_label_schema():
    surface_label = SurfaceLabel(
        [atf.Status.CORRECTION], atf.Surface.SURFACE, "stone wig"
    )
    dump = SurfaceLabelSchema().dump(surface_label)
    assert dump == {
        "status": ["CORRECTION"],
        "surface": "SURFACE",
        "text": "stone wig",
        "abbreviation": "stone wig",
    }
    assert SurfaceLabelSchema().load(dump) == surface_label


def test_load_and_dump_object_label_schema():
    object_label = ObjectLabel([atf.Status.CORRECTION], atf.Object.OBJECT, "stone wig")
    dump = ObjectLabelSchema().dump(object_label)
    assert dump == {
        "status": ["CORRECTION"],
        "object": "OBJECT",
        "text": "stone wig",
        "abbreviation": "stone wig",
    }
    assert ObjectLabelSchema().load(dump) == object_label
