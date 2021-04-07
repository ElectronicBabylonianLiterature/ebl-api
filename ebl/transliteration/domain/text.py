from itertools import zip_longest
from typing import Callable, Iterable, List, Mapping, Optional, Sequence, Tuple, Type

import attr

from ebl.merger import Merger
from ebl.transliteration.domain.atf import ATF_PARSER_VERSION, Atf
from ebl.transliteration.domain.at_line import ColumnAtLine, ObjectAtLine, SurfaceAtLine
from ebl.transliteration.domain.labels import ColumnLabel, SurfaceLabel, ObjectLabel
from ebl.lemmatization.domain.lemmatization import Lemmatization, LemmatizationError
from ebl.transliteration.domain.line import Line
from ebl.transliteration.domain.line_number import AbstractLineNumber
from ebl.transliteration.domain.text_line import TextLine


@attr.s(auto_attribs=True, frozen=True)
class Label:
    column: Optional[ColumnLabel]
    surface: Optional[SurfaceLabel]
    object: Optional[ObjectLabel]
    line_number: Optional[AbstractLineNumber]

    def set_column(self, column: Optional[ColumnLabel]) -> "Label":
        return attr.evolve(self, column=column)

    def set_surface(self, surface: Optional[SurfaceLabel]) -> "Label":
        return attr.evolve(self, surface=surface)

    def set_object(self, object: Optional[ObjectLabel]) -> "Label":
        return attr.evolve(self, object=object)

    def set_line_number(self, line_number: Optional[AbstractLineNumber]) -> "Label":
        return attr.evolve(self, line_number=line_number)


@attr.s(auto_attribs=True, frozen=True)
class Text:
    lines: Sequence[Line] = tuple()
    parser_version: str = ATF_PARSER_VERSION

    @property
    def number_of_lines(self) -> int:
        return len(self.text_lines)

    @property
    def text_lines(self) -> Sequence[TextLine]:
        return tuple(line for line in self.lines if isinstance(line, TextLine))

    @property
    def lemmatization(self) -> Lemmatization:
        return Lemmatization(tuple(line.lemmatization for line in self.lines))

    @property
    def atf(self) -> Atf:
        return Atf("\n".join(line.atf for line in self.lines))

    @property
    def labels(self,) -> Sequence[Label]:
        current: Label = Label(None, None, None, None)
        labels: List[Label] = []

        handlers: Mapping[Type[Line], Callable[[Line], Tuple[Label, List[Label]]]] = {
            TextLine: lambda line: (
                current,
                [*labels, current.set_line_number(line.line_number)],
            ),
            ColumnAtLine: lambda line: (current.set_column(line.column_label), labels),
            SurfaceAtLine: lambda line: (
                current.set_surface(line.surface_label),
                labels,
            ),
            ObjectAtLine: lambda line: (current.set_object(line.label), labels),
        }

        for line in self.lines:
            if type(line) in handlers:
                current, labels = handlers[type(line)](line)

        return labels

    def update_lemmatization(self, lemmatization: Lemmatization) -> "Text":
        if len(self.lines) == len(lemmatization.tokens):
            zipped = zip_longest(self.lines, lemmatization.tokens)
            lines = tuple(
                line.update_lemmatization(lemmas) for [line, lemmas] in zipped
            )
            return attr.evolve(self, lines=lines)
        else:
            raise LemmatizationError()

    def merge(self, other: "Text") -> "Text":
        def map_(line: Line) -> str:
            return line.key

        def inner_merge(old: Line, new: Line) -> Line:
            return old.merge(new)

        merged_lines = Merger(map_, inner_merge).merge(self.lines, other.lines)
        return attr.evolve(
            self, lines=tuple(merged_lines), parser_version=other.parser_version
        )

    def set_parser_version(self, parser_version: str) -> "Text":
        return attr.evolve(self, parser_version=parser_version)

    @staticmethod
    def of_iterable(
        lines: Iterable[Line], parser_version: str = ATF_PARSER_VERSION
    ) -> "Text":
        return Text(tuple(lines), parser_version)
