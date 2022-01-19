from typing import Optional

import attr

from ebl.transliteration.domain.labels import ColumnLabel, ObjectLabel, SurfaceLabel
from ebl.transliteration.domain.line_number import (
    AbstractLineNumber,
)


@attr.s(auto_attribs=True, frozen=True)
class LineLabel:
    column: Optional[ColumnLabel]
    surface: Optional[SurfaceLabel]
    object: Optional[ObjectLabel]
    line_number: Optional[AbstractLineNumber]

    def set_column(self, column: Optional[ColumnLabel]) -> "LineLabel":
        return attr.evolve(self, column=column)

    def set_surface(self, surface: Optional[SurfaceLabel]) -> "LineLabel":
        return attr.evolve(self, surface=surface)

    def set_object(self, object: Optional[ObjectLabel]) -> "LineLabel":
        return attr.evolve(self, object=object)

    def set_line_number(self, line_number: Optional[AbstractLineNumber]) -> "LineLabel":
        return attr.evolve(self, line_number=line_number)
