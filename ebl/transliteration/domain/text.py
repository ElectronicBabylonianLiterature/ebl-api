from itertools import combinations, groupby, zip_longest
from typing import Callable, Iterable, List, Mapping, Sequence, Tuple, Type, cast

import attr

from ebl.lemmatization.domain.lemmatization import Lemmatization, LemmatizationError
from ebl.merger import Merger
from ebl.transliteration.domain.at_line import ColumnAtLine, ObjectAtLine, SurfaceAtLine
from ebl.transliteration.domain.atf import ATF_PARSER_VERSION, Atf
from ebl.transliteration.domain.line import Line
from ebl.transliteration.domain.line_label import LineLabel
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.translation_line import Extent, TranslationLine


@attr.s(auto_attribs=True, frozen=True)
class Text:
    lines: Sequence[Line] = attr.ib(default=tuple())
    parser_version: str = ATF_PARSER_VERSION

    @lines.validator
    def _validate_extents(self, _, value: Sequence[Line]) -> None:
        labels = [
            (label.column, label.surface, label.line_number) for label in self.labels
        ]
        index = -1
        errors = []
        ranges = []

        for line in value:
            if isinstance(line, TextLine):
                index += 1
            elif isinstance(line, TranslationLine):
                if index < 0:
                    errors.append('Translation "{line.atf}" before any text line.')

                if line.extent:
                    extent: Extent = cast(Extent, line.extent)
                    try:
                        end = labels.index(
                            (extent.column, extent.surface, extent.number)
                        )
                        if end <= index:
                            errors.append(f"Extent ${extent} before translation.")
                        ranges.append((line.language, set(range(index, end + 1))))
                    except ValueError:
                        errors.append(f"Extent ${extent} does not exist.")
                else:
                    ranges.append((line.language, set(range(index, index + 1))))

        errors.extend(
            f"Overlapping extents for language {group}."
            for key, group in groupby(ranges, lambda pair: pair[0])
            if any(pair[0][1] & pair[1][1] for pair in combinations(group, 2))
        )

        if errors:
            raise ValueError(" ".join(errors))

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
    def labels(self,) -> Sequence[LineLabel]:
        current: LineLabel = LineLabel(None, None, None, None)
        labels: List[LineLabel] = []

        handlers: Mapping[
            Type[Line], Callable[[Line], Tuple[LineLabel, List[LineLabel]]]
        ] = {
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
