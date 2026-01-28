from enum import Enum, unique
from typing import Iterator, Mapping, Optional, Sequence, Tuple, TypeVar, Union, Set

import attr
import pydash

import ebl.corpus.domain.chapter_validators as validators
from ebl.corpus.domain.extant_line import ExtantLine
from ebl.corpus.domain.line import Line
from ebl.corpus.domain.manuscript_line import ManuscriptLineLabel, ManuscriptLine
from ebl.corpus.domain.manuscript import Manuscript, Siglum
from ebl.corpus.domain.record import Record
from ebl.errors import NotFoundError
from ebl.merger import Merger
from ebl.transliteration.domain.markup import MarkupPart, to_title
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.common.domain.stage import Stage
from ebl.transliteration.domain.text_id import TextId
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.translation_line import (
    DEFAULT_LANGUAGE,
    TranslationLine,
)
from ebl.transliteration.domain.transliteration_query import TransliterationQuery
from ebl.corpus.domain.chapter_query import ChapterQueryColophonLines

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

    def to_tuple(self) -> Tuple[str, int, int, str, str]:
        return (
            self.text_id.genre.value,
            self.text_id.category,
            self.text_id.index,
            self.stage.long_name,
            self.name,
        )

    def __str__(self) -> str:
        return f"{self.text_id} {self.stage.abbreviation} {self.name}"


def make_title(translation: Sequence[TranslationLine]) -> Sequence[MarkupPart]:
    return next(
        (
            to_title(line.parts)
            for line in translation
            if line.language == DEFAULT_LANGUAGE
        ),
        (),
    )


@attr.s(auto_attribs=True, frozen=True)
class Chapter:
    text_id: TextId
    classification: Classification = Classification.ANCIENT
    stage: Stage = Stage.NEO_ASSYRIAN
    version: str = ""
    name: str = ""
    order: int = 0
    manuscripts: Sequence[Manuscript] = attr.ib(
        default=(),
        validator=[
            validators.validate_manuscript_ids,
            validators.validate_manuscript_sigla,
        ],
    )
    uncertain_fragments: Sequence[MuseumNumber] = ()
    lines: Sequence[Line] = attr.ib(
        default=(),
        validator=[
            validators.validate_line_numbers,
            validators.validate_translations,
            validators.validate_orphan_manuscript_ids,
            validators.validate_manuscript_line_labels,
        ],
    )
    signs: Sequence[Optional[str]] = ()
    record: Record = Record()
    parser_version: str = ""
    is_filtered_query: bool = False
    colophon_lines_in_query: ChapterQueryColophonLines = attr.ib(
        default=ChapterQueryColophonLines()
    )
    text_name: str = ""

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
            for number, line in enumerate([] if signs is None else signs.split("\n"))
            if "?" in line
        ]

    @property
    def extant_lines(self) -> Mapping[Siglum, Mapping[ManuscriptLineLabel, ExtantLine]]:
        return {
            manuscript.siglum: self._get_extant_lines(manuscript.id)
            for manuscript in self.manuscripts
        }

    @property
    def manuscript_line_labels(self) -> Sequence[ManuscriptLineLabel]:
        return [label for line in self.lines for label in line.manuscript_line_labels]

    def get_manuscript(self, id_: int) -> Manuscript:
        try:
            return next(
                manuscript for manuscript in self.manuscripts if manuscript.id == id_
            )
        except StopIteration as error:
            raise NotFoundError(f"No manuscripts with id {id_}.") from error

    def get_matching_lines(self, query: TransliterationQuery) -> Sequence[Line]:
        if self.is_filtered_query:
            return self.lines
        return [
            self.lines[index]
            for index in sorted(self._get_matching_line_indexes(query))
        ]

    def _get_matching_line_indexes(self, query: TransliterationQuery) -> Set[int]:
        return {
            line.source
            for index, numbers in enumerate(self._match(query))
            for start, end in numbers
            for line in self.text_lines[index][start : end + 1]
            if line.source is not None
        }

    def get_matching_colophon_lines(
        self, query: TransliterationQuery
    ) -> Mapping[int, Sequence[TextLine]]:
        if self.is_filtered_query:
            return self.colophon_lines_in_query.get_matching_lines(self.manuscripts)
        return self._get_matching_colophon_lines(query)

    def _get_matching_colophon_lines(
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

    def _get_extant_lines(
        self, manuscript_id: int
    ) -> Mapping[ManuscriptLineLabel, ExtantLine]:
        return pydash.group_by(
            (
                ExtantLine.of(line, manuscript_id)
                for line in self.lines
                if manuscript_id in line.manuscript_ids
                and line.get_manuscript_text_line(manuscript_id) is not None
            ),
            lambda extant_line: extant_line.label,
        )

    def _get_manuscript_text_lines(
        self, manuscript: Manuscript
    ) -> Sequence[TextLineEntry]:
        def create_entries(index: int, line: Line) -> Iterator[TextLineEntry]:
            for text_line in line.get_manuscript_text_lines(manuscript.id):
                yield TextLineEntry(text_line, index)

        entries = [
            entry
            for index, line in enumerate(self.lines)
            for entry in create_entries(index, line)
        ]

        return entries + [TextLineEntry(line, None) for line in manuscript.text_lines]

    def _match(
        self, query: TransliterationQuery
    ) -> Sequence[Sequence[Tuple[int, int]]]:
        return [query.match(signs) for signs in self.signs if signs is not None]
