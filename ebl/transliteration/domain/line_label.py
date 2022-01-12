from typing import Optional

import attr
from singledispatchmethod import singledispatchmethod

from ebl.transliteration.domain.labels import ColumnLabel, ObjectLabel, SurfaceLabel
from ebl.transliteration.domain.line_number import (
    AbstractLineNumber,
    LineNumberRange,
    LineNumber,
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

    @singledispatchmethod
    def handle_line_number(self, line_number: AbstractLineNumber, number: int) -> bool:
        raise ValueError("No default for overloading")

    @handle_line_number.register(LineNumber)
    def _(self, line_number: LineNumber, number: int):
        return number == line_number.number

    @handle_line_number.register(LineNumberRange)
    def _(self, line_number: LineNumberRange, number: int):
        return line_number.start.number <= number <= line_number.end.number

    def is_line_number(self, line_number_to_match: int) -> bool:
        return (
            self.handle_line_number(self.line_number, line_number_to_match)
            if self.line_number
            else False
        )
