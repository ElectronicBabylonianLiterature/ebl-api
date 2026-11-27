from dataclasses import dataclass
from typing import Sequence

import attr
import pytest

from ebl.bibliography.application.bibliography import Bibliography
from ebl.corpus.application.chapter_edit_writer import ChapterEditWriter
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.manuscript import Manuscript
from ebl.corpus.domain.manuscripts_update import ManuscriptsUpdate
from ebl.corpus.domain.parser import parse_chapter
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.errors import DataError
from ebl.provenance.application.provenance_service import ProvenanceService
from ebl.tests.corpus.corpus_test_support import (
    CHAPTER,
    CHAPTER_WITHOUT_DOCUMENTS,
    UpdateDependencies,
    When,
    expect_bibliography,
    expect_find_and_update_chapter,
    expect_invalid_references,
)
from ebl.tests.corpus.support import ANY_USER
from ebl.transliteration.domain.atf import ATF_PARSER_VERSION
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.text import Text as Transliteration
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.word_tokens import Word


@dataclass(frozen=True)
class WriterDependencies:
    writer: ChapterEditWriter
    update: UpdateDependencies
    provenance_service: ProvenanceService


@pytest.fixture
def dependencies(request: pytest.FixtureRequest) -> WriterDependencies:
    return WriterDependencies(
        writer=request.getfixturevalue("writer"),
        update=UpdateDependencies.of(request),
        provenance_service=request.getfixturevalue("seeded_provenance_service"),
    )


def expect_update(dependencies: WriterDependencies, updated_chapter: Chapter) -> None:
    expect_find_and_update_chapter(
        dependencies.update, CHAPTER_WITHOUT_DOCUMENTS, updated_chapter
    )


def test_updating_manuscripts(dependencies: WriterDependencies) -> None:
    uncertain_fragments = (MuseumNumber.of("K.1"),)
    updated_chapter = attr.evolve(
        CHAPTER,
        manuscripts=(
            attr.evolve(
                CHAPTER.manuscripts[0],
                colophon=Transliteration.of_iterable(
                    [
                        TextLine.of_iterable(
                            LineNumber(1, True), (Word.of([Reading.of_name("ba")]),)
                        )
                    ]
                ),
                unplaced_lines=Transliteration.of_iterable(
                    [
                        TextLine.of_iterable(
                            LineNumber(1, True), (Word.of([Reading.of_name("ku")]),)
                        )
                    ]
                ),
                notes="Updated manuscript.",
            ),
        ),
        uncertain_fragments=uncertain_fragments,
        signs=("KU ABZ075 ABZ207a\\u002F207b\\u0020X\nBA\nKU",),
    )
    expect_update(dependencies, updated_chapter)

    manuscripts = (updated_chapter.manuscripts[0],)
    assert (
        dependencies.writer.save_manuscripts(
            CHAPTER.id_,
            ManuscriptsUpdate(manuscripts, uncertain_fragments),
            None,
            dependencies.update.user,
        ).chapter
        == updated_chapter
    )


@pytest.mark.parametrize(
    "manuscripts",
    [
        (),
        (
            CHAPTER_WITHOUT_DOCUMENTS.manuscripts[0],
            CHAPTER_WITHOUT_DOCUMENTS.manuscripts[0],
        ),
    ],
)
def test_invalid_manuscripts(
    manuscripts: Sequence[Manuscript],
    writer: ChapterEditWriter,
    text_repository: MongoTextRepository,
    bibliography: Bibliography,
    when: When,
) -> None:
    when(text_repository).find_chapter(CHAPTER.id_).thenReturn(
        CHAPTER_WITHOUT_DOCUMENTS
    )
    expect_bibliography(bibliography, when)
    with pytest.raises(DataError):
        writer.save_manuscripts(
            CHAPTER.id_, ManuscriptsUpdate(manuscripts, ()), None, ANY_USER
        )


def test_update_manuscripts_raises_exception_if_invalid_references(
    writer: ChapterEditWriter,
    text_repository: MongoTextRepository,
    bibliography: Bibliography,
    when: When,
) -> None:
    manuscripts = CHAPTER.manuscripts
    expect_invalid_references(bibliography, when)

    with pytest.raises(DataError):
        writer.save_manuscripts(
            CHAPTER.id_, ManuscriptsUpdate(manuscripts, ()), None, ANY_USER
        )


def test_importing_lines(dependencies: WriterDependencies) -> None:
    line_number = CHAPTER_WITHOUT_DOCUMENTS.lines[-1].number.number + 1
    siglum = CHAPTER_WITHOUT_DOCUMENTS.manuscripts[0].siglum
    atf = f"{line_number}. kur\n{siglum} {line_number}. ba"
    updated_chapter = attr.evolve(
        CHAPTER,
        lines=(  # pyre-ignore[60]
            *(line.set_variant_alignment_flags() for line in CHAPTER.lines),
            *parse_chapter(atf, CHAPTER.manuscripts, dependencies.provenance_service),
        ),
        signs=("KU ABZ075 ABZ207a\\u002F207b\\u0020X\nBA\nKU\nABZ075",),
        parser_version=ATF_PARSER_VERSION,
    )
    expect_update(dependencies, updated_chapter)

    assert (
        dependencies.writer.save_imported_lines(
            CHAPTER.id_, atf, None, dependencies.update.user
        ).chapter
        == updated_chapter
    )
