from ebl.transliteration.application.line_schemas import (
    ScopeContainerSchema,
    StateDollarLineSchema,
    ColumnLabelSchema,
    SurfaceLabelSchema,
)
from ebl.transliteration.application.token_schemas import dump_tokens
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.dollar_line import ScopeContainer, StateDollarLine
from ebl.transliteration.domain.labels import ColumnLabel, SurfaceLabel
from ebl.transliteration.domain.tokens import ValueToken


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
