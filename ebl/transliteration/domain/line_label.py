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
    seal_number: Optional[int]
    line_index: Optional[int] = attr.ib(default=None, eq=False)

    def set_column(self, column: Optional[ColumnLabel]) -> "LineLabel":
        return attr.evolve(self, column=column)

    def set_surface(self, surface: Optional[SurfaceLabel]) -> "LineLabel":
        return attr.evolve(self, surface=surface)

    def set_object(self, object: Optional[ObjectLabel]) -> "LineLabel":
        return attr.evolve(self, object=object)

    def set_line_number(self, line_number: Optional[AbstractLineNumber]) -> "LineLabel":
        return attr.evolve(self, line_number=line_number)

    def set_line_index(self, index: Optional[int]) -> "LineLabel":
        return attr.evolve(self, line_index=index)

    def set_seal(self, seal_number: Optional[int]) -> "LineLabel":
        return attr.evolve(self, seal_number=seal_number)

    @property
    def formatted_label(self) -> str:
        line_number = self.line_number
        column = self.column
        surface = self.surface
        object = self.object
        line_atf = line_number.atf if line_number else ""
        column_abbr = column.abbreviation if column else ""
        surface_abbr = surface.abbreviation if surface else ""
        object_abbr = object.abbreviation if object else ""
        return " ".join(
            filter(
                bool,
                [column_abbr, surface_abbr, object_abbr, line_atf.replace(".", "")],
            )
        )
