from typing import Optional, Sequence

import attr

from ebl.common.domain.stage import Stage
from ebl.corpus.domain.chapter import Chapter, Classification
from ebl.corpus.domain.chapter_revision import LEGACY_REVISION
from ebl.corpus.domain.line import Line
from ebl.corpus.domain.line_atf import reconstruction_to_atf, translation_to_atf
from ebl.corpus.domain.line_variant import LineVariant
from ebl.corpus.domain.manuscript import Manuscript
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.domain.text_id import TextId


def museum_number_to_string(museum_number: Optional[MuseumNumber]) -> str:
    return str(museum_number) if museum_number else ""


@attr.s(frozen=True, auto_attribs=True)
class ManuscriptOutline:
    id: int
    siglum: str
    museum_number: str
    accession: str

    @staticmethod
    def of_manuscript(manuscript: Manuscript) -> "ManuscriptOutline":
        return ManuscriptOutline(
            manuscript.id,
            str(manuscript.siglum),
            museum_number_to_string(manuscript.museum_number),
            manuscript.accession,
        )


@attr.s(frozen=True, auto_attribs=True)
class LineVariantOutline:
    reconstruction: str
    manuscript_ids: Sequence[int]

    @staticmethod
    def of_variant(variant: LineVariant) -> "LineVariantOutline":
        return LineVariantOutline(
            reconstruction_to_atf(
                variant.reconstruction, variant.note, variant.parallel_lines
            ),
            tuple(variant.manuscript_ids),
        )


@attr.s(frozen=True, auto_attribs=True)
class LineOutline:
    index: int
    number: str
    is_second_line_of_parallelism: bool
    is_beginning_of_section: bool
    translation: str
    variants: Sequence[LineVariantOutline]

    @staticmethod
    def of_line(index: int, line: Line) -> "LineOutline":
        return LineOutline(
            index,
            line.number.label,
            line.is_second_line_of_parallelism,
            line.is_beginning_of_section,
            translation_to_atf(line.translation),
            tuple(map(LineVariantOutline.of_variant, line.variants)),
        )


@attr.s(frozen=True, auto_attribs=True)
class ChapterOutline:
    text_id: TextId
    classification: Classification
    stage: Stage
    version: str
    name: str
    order: int
    uncertain_fragments: Sequence[str]
    manuscripts: Sequence[ManuscriptOutline]
    lines: Sequence[LineOutline]
    revision: str = LEGACY_REVISION

    @staticmethod
    def of_chapter(
        chapter: Chapter, revision: str = LEGACY_REVISION
    ) -> "ChapterOutline":
        return ChapterOutline(
            chapter.text_id,
            chapter.classification,
            chapter.stage,
            chapter.version,
            chapter.name,
            chapter.order,
            tuple(map(museum_number_to_string, chapter.uncertain_fragments)),
            tuple(map(ManuscriptOutline.of_manuscript, chapter.manuscripts)),
            tuple(
                LineOutline.of_line(index, line)
                for index, line in enumerate(chapter.lines)
            ),
            revision,
        )
