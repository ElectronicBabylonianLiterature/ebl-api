from collections import defaultdict
from functools import singledispatchmethod
from typing import DefaultDict, Iterator, List, Protocol, Sequence, Tuple

import pydash

from ebl.transliteration.domain.line import Line
from ebl.transliteration.domain.line_label import LineLabel
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.translation_line import Extent, TranslationLine
from ebl.transliteration.domain.transliteration_error import (
    ErrorAnnotation,
    ExtentLabelError,
)


class HasLabels(Protocol):
    labels: Sequence[LineLabel]


class LabelsValidator:
    def __init__(self, text: HasLabels) -> None:
        self._index = -1
        self._ranges: DefaultDict[str, List[Tuple[int, int]]] = defaultdict(list)
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


def _validate_extents(instance, _attribute, value: Sequence[Line]) -> None:
    if errors := LabelsValidator(instance).get_errors(value):
        raise ExtentLabelError(errors)
