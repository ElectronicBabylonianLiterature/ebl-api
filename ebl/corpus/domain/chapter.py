from enum import Enum, unique
import itertools
from typing import Mapping, Optional, Sequence, Tuple, TypeVar, Union, cast

import attr
import pydash

from ebl.corpus.domain.line import Line, ManuscriptLine, ManuscriptLineLabel
from ebl.corpus.domain.manuscript import Manuscript, Siglum
from ebl.corpus.domain.stage import Stage
from ebl.errors import NotFoundError
from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.merger import Merger
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.transliteration_query import TransliterationQuery
from ebl.corpus.domain.text_id import TextId
from ebl.transliteration.domain.translation_line import Extent


ChapterItem = Union["Chapter", Manuscript, Line, ManuscriptLine]


class ChapterVisitor:
    def visit(self, item: ChapterItem) -> None:
        pass


@unique
class Classification(Enum):
    ANCIENT = "Ancient"
    MODERN = "Modern"


T = TypeVar("T")


@attr.s(auto_attribs=True, frozen=True)
class TextLineEntry:
    line: TextLine
    source: Optional[int] = None


@attr.s(auto_attribs=True, frozen=True)
class ChapterId:
    text_id: TextId
    stage: Stage
    name: str

    def to_tuple(self) -> Tuple[int, int, str, str]:
        return (self.text_id.category, self.text_id.index, self.stage.value, self.name)

    def __str__(self) -> str:
        return f"{self.text_id} {self.stage} {self.name}"


@attr.s(auto_attribs=True, frozen=True)
class Chapter:
    text_id: TextId
    classification: Classification = Classification.ANCIENT
    stage: Stage = Stage.NEO_ASSYRIAN
    version: str = ""
    name: str = ""
    order: int = 0
    manuscripts: Sequence[Manuscript] = attr.ib(default=tuple())
    uncertain_fragments: Sequence[MuseumNumber] = tuple()
    lines: Sequence[Line] = attr.ib(default=tuple())
    signs: Sequence[str] = tuple()
    parser_version: str = ""

    @manuscripts.validator
    def _validate_manuscript_ids(self, _, value: Sequence[Manuscript]) -> None:
        duplicate_ids = pydash.duplicates([manuscript.id for manuscript in value])
        if duplicate_ids:
            raise ValueError(f"Duplicate manuscript IDs: {duplicate_ids}.")

    @manuscripts.validator
    def _validate_manuscript_sigla(self, _, value: Sequence[Manuscript]) -> None:
        duplicate_sigla = pydash.duplicates([manuscript.siglum for manuscript in value])
        if duplicate_sigla:
            raise ValueError(f"Duplicate sigla: {duplicate_sigla}.")

    @lines.validator
    def _validate_orphan_manuscript_ids(self, _, value: Sequence[Line]) -> None:
        manuscript_ids = {manuscript.id for manuscript in self.manuscripts}
        used_manuscripts_ids = {
            manuscript_id
            for line in self.lines
            for manuscript_id in line.manuscript_ids
        }
        orphans = used_manuscripts_ids - manuscript_ids
        if orphans:
            raise ValueError(f"Missing manuscripts: {orphans}.")

    @lines.validator
    def _validate_line_numbers(self, _, value: Sequence[Line]) -> None:
        duplicates = pydash.duplicates([line.number for line in value])
        if any(duplicates):
            raise ValueError(f"Duplicate line numbers: {duplicates}.")

    @lines.validator
    def _validate_manuscript_line_labels(self, _, value: Sequence[Line]) -> None:
        duplicates = pydash.duplicates(self._manuscript_line_labels)
        if duplicates:
            readable_labels = self._make_labels_readable(duplicates)
            raise ValueError(f"Duplicate manuscript line labels: {readable_labels}.")

    @lines.validator
    def _validate_extents(self, _, value: Sequence[Line]) -> None:
        line_numbers = {line.number: index for index, line in enumerate(value)}
        errors = [
            f"Invalid extent {translation.extent} in line {line.number}."
            for index, line in enumerate(value)
            for translation in line.translation
            if translation.extent
            and line_numbers.get(cast(Extent, translation.extent).number, -1) < index
        ]

        if errors:
            raise ValueError(" ".join(errors))

        ranges = itertools.groupby(
            [
                (
                    translation.language,
                    set(
                        range(
                            index,
                            (
                                translation.extent
                                and line_numbers[
                                    cast(Extent, translation.extent).number
                                ]
                                or index
                            )
                            + 1,
                        )
                    ),
                )
                for index, line in enumerate(value)
                for translation in line.translation
            ],
            lambda pair: pair[0],
        )

        range_errors = [
            f"Overlapping extents for language {group}."
            for key, group in ranges
            if any(pair[0][1] & pair[1][1] for pair in itertools.combinations(group, 2))
        ]

        if range_errors:
            raise ValueError(" ".join(range_errors))

    @property
    def id_(self) -> ChapterId:
        return ChapterId(self.text_id, self.stage, self.name)

    @property
    def text_lines(self) -> Sequence[Sequence[TextLineEntry]]:
        return [
            self._get_manuscript_text_lines(manuscript)
            for manuscript in self.manuscripts
        ]

    @property
    def invalid_lines(self) -> Sequence[Tuple[Siglum, TextLineEntry]]:
        text_lines = self.text_lines
        return [
            (self.manuscripts[index].siglum, text_lines[index][number])
            for index, signs in enumerate(self.signs)
            for number, line in enumerate(signs.split("\n"))
            if "?" in line
        ]

    @property
    def _manuscript_line_labels(self) -> Sequence[ManuscriptLineLabel]:
        return [label for line in self.lines for label in line.manuscript_line_labels]

    def get_matching_lines(self, query: TransliterationQuery) -> Sequence[Line]:
        text_lines = self.text_lines
        matching_indices = {
            cast(int, line.source)
            for index, numbers in enumerate(self._match(query))
            for start, end in numbers
            for line in text_lines[index][start : end + 1]
            if line.source is not None
        }
        return [self.lines[index] for index in sorted(matching_indices)]

    def get_matching_colophon_lines(
        self, query: TransliterationQuery
    ) -> Mapping[int, Sequence[TextLine]]:
        text_lines = self.text_lines

        return pydash.omit_by(
            {
                self.manuscripts[index].id: [
                    line.line
                    for start, end in numbers
                    for line in text_lines[index][start : end + 1]
                    if line.source is None
                ]
                for index, numbers in enumerate(self._match(query))
            },
            pydash.is_empty,
        )

    def merge(self, other: "Chapter") -> "Chapter":
        def inner_merge(old: Line, new: Line) -> Line:
            return old.merge(new)

        merged_lines = Merger(repr, inner_merge).merge(self.lines, other.lines)
        return attr.evolve(other, lines=tuple(merged_lines))

    def _get_manuscript_text_lines(
        self, manuscript: Manuscript
    ) -> Sequence[TextLineEntry]:
        def create_entry(line: Line, index: int) -> Optional[TextLineEntry]:
            text_line = line.get_manuscript_text_line(manuscript.id)
            return text_line and TextLineEntry(text_line, index)

        return (
            pydash.chain(self.lines)
            .map_(create_entry)
            .reject(pydash.is_none)
            .concat(
                [TextLineEntry(line, None) for line in manuscript.colophon_text_lines]
            )
            .value()
        )

    def _get_manuscript(self, id_: int) -> Manuscript:
        try:
            return next(
                manuscript for manuscript in self.manuscripts if manuscript.id == id_
            )
        except StopIteration:
            raise NotFoundError(f"No manuscripts with id {id_}.")

    def _make_labels_readable(self, labels: Sequence[ManuscriptLineLabel]) -> str:
        return ", ".join(
            " ".join(
                [
                    str(self._get_manuscript(label[0]).siglum),
                    *[side.to_value() for side in label[1]],
                    label[2].label,
                ]
            )
            for label in labels
        )

    def _match(
        self, query: TransliterationQuery
    ) -> Sequence[Sequence[Tuple[int, int]]]:
        return [query.match(signs) for signs in self.signs]
