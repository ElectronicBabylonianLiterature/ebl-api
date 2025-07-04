from functools import singledispatchmethod
from itertools import count, zip_longest
from collections import defaultdict
from typing import Callable, Iterable, List, Mapping, Sequence, Tuple, Type, Iterator

import pydash
import attr

from ebl.fragmentarium.domain.token_annotation import TextLemmaAnnotation
from ebl.lemmatization.domain.lemmatization import Lemmatization, LemmatizationError
from ebl.merger import Merger
from ebl.transliteration.domain.at_line import (
    ColumnAtLine,
    ObjectAtLine,
    SurfaceAtLine,
    SealAtLine,
)
from ebl.transliteration.domain.transliteration_error import (
    ErrorAnnotation,
    ExtentLabelError,
)
from ebl.transliteration.domain.atf import ATF_PARSER_VERSION, Atf
from ebl.transliteration.domain.line import Line
from ebl.transliteration.domain.line_label import LineLabel
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.translation_line import Extent, TranslationLine
from ebl.transliteration.domain.word_tokens import AbstractWord


class LabelsValidator:
    def __init__(self, text: "Text") -> None:
        self._index = -1
        self._ranges = defaultdict(list)
        self._errors: List[ErrorAnnotation] = []
        self._labels = [
            (label.column, label.surface, label.line_number) for label in text.labels
        ]

    def get_errors(self, lines: Sequence[Line]) -> List[ErrorAnnotation]:
        self._index = -1
        self._ranges = defaultdict(list)
        self._errors = []

        for index, line in enumerate(lines):
            self._validate_line(line, index)

        return [*self._errors, *self._get_overlaps()]

    def _get_overlaps(self) -> Iterator[ErrorAnnotation]:
        for language, ranges in self._ranges.items():
            overlap = pydash.duplicates([index for index, _ in ranges])

            yield from (
                ErrorAnnotation(
                    f"Overlapping extents for language {language}.",
                    annotation_index + 1,
                )
                for index, annotation_index in ranges
                if index in overlap
            )

    def _get_index(self, extent: Extent) -> int:
        return self._labels.index((extent.column, extent.surface, extent.number))

    @singledispatchmethod
    def _validate_line(self, line: Line, annotation_index: int) -> None:
        pass

    @_validate_line.register(TextLine)
    def _(self, line: TextLine, annotation_index: int) -> None:
        self._index += 1

    @_validate_line.register(TranslationLine)
    def _(self, line: TranslationLine, annotation_index: int) -> None:
        if self._index < 0:
            self._errors.append(
                ErrorAnnotation(
                    "Translation before any text line.",
                    annotation_index + 1,
                )
            )

        if line.extent:
            self._validate_extent(line, line.extent, annotation_index)
        else:
            self._ranges[line.language].append((self._index, annotation_index))

    def _validate_extent(
        self, line: TranslationLine, extent: Extent, annotation_index: int
    ) -> None:
        try:
            end = self._get_index(extent)
            if end <= self._index:
                self._errors.append(
                    ErrorAnnotation(
                        f"Extent {extent} before translation.",
                        annotation_index + 1,
                    )
                )
            self._ranges[line.language].extend(
                (index, annotation_index) for index in range(self._index, end + 1)
            )
        except ValueError:
            self._errors.append(
                ErrorAnnotation(
                    f"Extent {extent} does not exist.",
                    annotation_index + 1,
                )
            )


@attr.s(auto_attribs=True, frozen=True)
class Text:
    lines: Sequence[Line] = attr.ib(default=())
    parser_version: str = ATF_PARSER_VERSION

    @lines.validator
    def _validate_extents(self, _, value: Sequence[Line]) -> None:
        if errors := LabelsValidator(self).get_errors(value):
            raise ExtentLabelError(errors)

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
    def labels(self) -> Sequence[LineLabel]:
        current: LineLabel = LineLabel(None, None, None, None, None)
        labels: List[LineLabel] = []

        handlers: Mapping[
            Type[Line], Callable[[Line], Tuple[LineLabel, List[LineLabel]]]
        ] = {
            TextLine: lambda line: (
                current,
                [
                    *labels,
                    current.set_line_number(line.line_number),
                ],
            ),
            ColumnAtLine: lambda line: (current.set_column(line.column_label), labels),
            SurfaceAtLine: lambda line: (
                current.set_surface(line.surface_label),
                labels,
            ),
            ObjectAtLine: lambda line: (current.set_object(line.label), labels),
            SealAtLine: lambda line: (current.set_seal(line.number), labels),
        }

        for index, line in enumerate(self.lines):
            if type(line) in handlers:
                current = current.set_line_index(index)
                current, labels = handlers[type(line)](line)
        return labels

    @property
    def is_empty(self) -> bool:
        return len(self.lines) == 0

    def update_lemmatization(self, lemmatization: Lemmatization) -> "Text":
        if len(self.lines) == len(lemmatization.tokens):
            zipped = zip_longest(self.lines, lemmatization.tokens)
            lines = tuple(
                line.update_lemmatization(lemmas) for [line, lemmas] in zipped
            )
            return attr.evolve(self, lines=lines)
        else:
            raise LemmatizationError()

    def update_lemma_annotation(self, annotation: TextLemmaAnnotation) -> "Text":
        lines = tuple(
            (
                line.update_lemma_annotation(annotation[line_index])
                if line_index in annotation
                else line
            )
            for line_index, line in enumerate(self.lines)
        )
        return attr.evolve(self, lines=lines)

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

    def set_token_ids(self) -> "Text":
        start_id = (
            max(
                (
                    int(token.id_.split("-")[1]) if token.id_ else 0
                    for line in self.lines
                    if isinstance(line, TextLine)
                    for token in line.content
                    if isinstance(token, AbstractWord)
                ),
                default=0,
            )
            + 1
        )
        word_id = count(start_id)

        def set_word_ids(line: Line) -> Line:
            if isinstance(line, TextLine):
                tokens = tuple(
                    (
                        attr.evolve(token, id_=f"Word-{next(word_id)}")
                        if isinstance(token, AbstractWord) and token.id_ is None
                        else token
                    )
                    for token in line.content
                )
                return attr.evolve(line, content=tokens)
            return line

        lines = tuple(set_word_ids(line) for line in self.lines)

        return attr.evolve(self, lines=lines)

    @staticmethod
    def of_iterable(
        lines: Iterable[Line], parser_version: str = ATF_PARSER_VERSION
    ) -> "Text":
        return Text(tuple(lines), parser_version)
