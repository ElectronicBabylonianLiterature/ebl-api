from typing import (
    Callable, FrozenSet, Iterable, List, Mapping, Optional, Sequence, Tuple, Type
)

import attr
import pydash  # pyre-ignore

from ebl.merger import Merger
from ebl.transliteration.domain.atf import ATF_PARSER_VERSION, Atf, Object
from ebl.transliteration.domain.at_line import ColumnAtLine, ObjectAtLine, SurfaceAtLine
from ebl.transliteration.domain.labels import ColumnLabel, Status, SurfaceLabel
from ebl.transliteration.domain.lemmatization import (
    Lemmatization,
    LemmatizationError,
)
from ebl.transliteration.domain.line import Line
from ebl.transliteration.domain.line_number import AbstractLineNumber
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.word_tokens import Word


Label = Tuple[
    Optional[ColumnLabel],
    Optional[SurfaceLabel],
    Optional[Tuple[Object, FrozenSet[Status], str]],
    Optional[AbstractLineNumber],
]


@attr.s(auto_attribs=True, frozen=True)
class Text:
    lines: Sequence[Line] = tuple()
    parser_version: str = ATF_PARSER_VERSION

    @property
    def lemmatization(self) -> Lemmatization:
        return Lemmatization.from_list(
            [
                [
                    (
                        {"value": token.value, "uniqueLemma": list(token.unique_lemma),}
                        if isinstance(token, Word)
                        else {"value": token.value}
                    )
                    for token in line.content
                ]
                for line in self.lines
            ]
        )

    @property
    def atf(self) -> Atf:
        return Atf("\n".join(line.atf for line in self.lines))

    @property
    def labels(self,) -> Sequence[Label]:
        current: Label = (None, None, None, None)
        labels: List[Label] = []

        handlers: Mapping[Type[Line], Callable[[Line], Tuple[Label, List[Label]]]] = {
            TextLine: lambda line: (current,
                                    [*labels, (*current[:-1], line.line_number)]),
            ColumnAtLine: lambda line: ((line.column_label, *current[1:]), labels),
            SurfaceAtLine: lambda line: ((current[0], line.surface_label, *current[2:]),
                                         labels),
            ObjectAtLine: lambda line: ((
                *current[:2],
                (line.object_label, frozenset(line.status), line.text),
                current[-1],
            ), labels),
        }

        for line in self.lines:
            if type(line) in handlers:
                current, labels = handlers[type(line)](line)

        return labels

    def update_lemmatization(self, lemmatization: Lemmatization) -> "Text":
        if len(self.lines) == len(lemmatization.tokens):
            zipped = pydash.zip_(list(self.lines), list(lemmatization.tokens))
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
            self, lines=tuple(merged_lines), parser_version=other.parser_version,
        )

    def set_parser_version(self, parser_version: str) -> "Text":
        return attr.evolve(self, parser_version=parser_version)

    @staticmethod
    def of_iterable(
        lines: Iterable[Line], parser_version: str = ATF_PARSER_VERSION
    ) -> "Text":
        return Text(tuple(lines), parser_version)
