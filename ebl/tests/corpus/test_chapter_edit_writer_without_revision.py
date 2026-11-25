from dataclasses import dataclass
from typing import Any

import attr
import pytest

from ebl.corpus.application.chapter_edit_writer import ChapterEditWriter
from ebl.corpus.domain.manuscripts_update import ManuscriptsUpdate
from ebl.corpus.domain.parser import parse_chapter
from ebl.errors import DataError
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.tests.corpus.support import ANY_USER
from ebl.transliteration.domain.atf import ATF_PARSER_VERSION
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.text import Text as Transliteration
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.word_tokens import Word


from ebl.tests.corpus.test_corpus import (
    CHAPTER,
    CHAPTER_WITHOUT_DOCUMENTS,
    expect_bibliography,
    expect_find_and_update_chapter,
    expect_invalid_references,
)


@dataclass(frozen=True)
class ImportingLinesDependencies:
    writer: ChapterEditWriter
    text_repository: Any
    bibliography: Any
    changelog: Any
    signs: Any
    sign_repository: Any
    user: Any
    when: Any
    provenance_service: Any


@pytest.fixture
def importing_lines_dependencies(
    request: pytest.FixtureRequest,
) -> ImportingLinesDependencies:
    return ImportingLinesDependencies(
        writer=request.getfixturevalue("writer"),
        text_repository=request.getfixturevalue("text_repository"),
        bibliography=request.getfixturevalue("bibliography"),
        changelog=request.getfixturevalue("changelog"),
        signs=request.getfixturevalue("signs"),
        sign_repository=request.getfixturevalue("sign_repository"),
        user=request.getfixturevalue("user"),
        when=request.getfixturevalue("when"),
        provenance_service=request.getfixturevalue("seeded_provenance_service"),
    )


def test_updating_manuscripts(
    writer, text_repository, bibliography, changelog, signs, sign_repository, user, when
) -> None:
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
    expect_find_and_update_chapter(
        bibliography,
        changelog,
        CHAPTER_WITHOUT_DOCUMENTS,
        updated_chapter,
        signs,
        sign_repository,
        text_repository,
        user,
        when,
    )

    manuscripts = (updated_chapter.manuscripts[0],)
    assert (
        writer.save_manuscripts(
            CHAPTER.id_, ManuscriptsUpdate(manuscripts, uncertain_fragments), None, user
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
    manuscripts, writer, text_repository, bibliography, when
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
    writer, text_repository, bibliography, when
) -> None:
    manuscripts = CHAPTER.manuscripts
    expect_invalid_references(bibliography, when)

    with pytest.raises(DataError):
        writer.save_manuscripts(
            CHAPTER.id_, ManuscriptsUpdate(manuscripts, ()), None, ANY_USER
        )


def test_importing_lines(
    importing_lines_dependencies: ImportingLinesDependencies,
) -> None:
    writer = importing_lines_dependencies.writer
    text_repository = importing_lines_dependencies.text_repository
    bibliography = importing_lines_dependencies.bibliography
    changelog = importing_lines_dependencies.changelog
    signs = importing_lines_dependencies.signs
    sign_repository = importing_lines_dependencies.sign_repository
    user = importing_lines_dependencies.user
    when = importing_lines_dependencies.when
    seeded_provenance_service = importing_lines_dependencies.provenance_service
    line_number = CHAPTER_WITHOUT_DOCUMENTS.lines[-1].number.number + 1
    siglum = CHAPTER_WITHOUT_DOCUMENTS.manuscripts[0].siglum
    atf = f"{line_number}. kur\n{siglum} {line_number}. ba"
    updated_chapter = attr.evolve(
        CHAPTER,
        lines=(  # pyre-ignore[60]
            *(line.set_variant_alignment_flags() for line in CHAPTER.lines),
            *parse_chapter(atf, CHAPTER.manuscripts, seeded_provenance_service),
        ),
        signs=("KU ABZ075 ABZ207a\\u002F207b\\u0020X\nBA\nKU\nABZ075",),
        parser_version=ATF_PARSER_VERSION,
    )
    expect_find_and_update_chapter(
        bibliography,
        changelog,
        CHAPTER_WITHOUT_DOCUMENTS,
        updated_chapter,
        signs,
        sign_repository,
        text_repository,
        user,
        when,
    )

    assert (
        writer.save_imported_lines(CHAPTER.id_, atf, None, user).chapter
        == updated_chapter
    )
