from enum import Enum, unique
from typing import Mapping, Optional, Sequence, Tuple, TypeVar, Union

import attr
import pydash

import ebl.corpus.domain.chapter_validators as validators
from ebl.corpus.domain.extant_line import ExtantLine
from ebl.corpus.domain.line import Line, ManuscriptLine, ManuscriptLineLabel
from ebl.corpus.domain.manuscript import Manuscript, Siglum
from ebl.corpus.domain.record import Record
from ebl.errors import NotFoundError
from ebl.merger import Merger
from ebl.transliteration.domain.markup import MarkupPart, to_title
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.domain.stage import Stage
from ebl.transliteration.domain.text_id import TextId
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.translation_line import (
    DEFAULT_LANGUAGE,
    TranslationLine,
)
from ebl.transliteration.domain.transliteration_query import TransliterationQuery

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
            self.stage.value,
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
        tuple(),
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
        default=tuple(),
        validator=[
            validators.validate_manuscript_ids,
            validators.validate_manuscript_sigla,
        ],
    )
    uncertain_fragments: Sequence[MuseumNumber] = tuple()
    lines: Sequence[Line] = attr.ib(
        default=tuple(),
        validator=[
            validators.validate_line_numbers,
            validators.validate_translations,
            validators.validate_orphan_manuscript_ids,
            validators.validate_manuscript_line_labels,
        ],
    )
    signs: Sequence[str] = tuple()
    record: Record = Record()
    parser_version: str = ""
    is_filtered_query: bool = False
    colophon_lines_in_query: dict = dict()

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
        return self._get_matching_lines(query)

    def _get_matching_lines(self, query: TransliterationQuery) -> Sequence[Line]:
        text_lines = self.text_lines
        matching_indices = {
            line.source
            for index, numbers in enumerate(self._match(query))
            for start, end in numbers
            for line in text_lines[index][start : end + 1]
            if line.source is not None
        }
        return [self.lines[index] for index in sorted(matching_indices)]

    def get_matching_colophon_lines(
        self, query: TransliterationQuery
    ) -> Mapping[int, Sequence[TextLine]]:
        if self.is_filtered_query:
            return self._get_matching_colophon_lines_filtered()
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

    def _get_matching_colophon_lines_filtered(self) -> Mapping[int, Sequence[TextLine]]:
        matching_colophon_lines = {}
        for manuscript in self.manuscripts:
            manuscript_id = str(manuscript.id)
            if manuscript_id in self.colophon_lines_in_query.keys():
                matching_colophon_lines = self._select_matching_colophon_lines_filtered(
                    manuscript_id, manuscript.colophon.lines, matching_colophon_lines
                )
        return matching_colophon_lines

    def _select_matching_colophon_lines_filtered(
        self,
        manuscript_id: str,
        manuscript_colophon_lines: Sequence,
        matching_colophon_lines: dict,
    ) -> Mapping[int, Sequence[TextLine]]:
        colophon_lines = [
            line for line in manuscript_colophon_lines if isinstance(line, TextLine)
        ]
        matching_colophon_lines[int(manuscript_id)] = [
            colophon_lines[idx] for idx in self.colophon_lines_in_query[manuscript_id]
        ]
        return matching_colophon_lines

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
        def create_entry(line: Line, index: int) -> Optional[TextLineEntry]:
            text_line = line.get_manuscript_text_line(manuscript.id)
            return TextLineEntry(text_line, index) if text_line else None

        return (
            pydash.chain(self.lines)
            .map_(create_entry)
            .reject(pydash.is_none)
            .concat([TextLineEntry(line, None) for line in manuscript.text_lines])
            .value()
        )

    def _match(
        self, query: TransliterationQuery
    ) -> Sequence[Sequence[Tuple[int, int]]]:
        return [query.match(signs) for signs in self.signs]
