import attr
import pytest

from ebl.bibliography.application.bibliography import Bibliography
from ebl.corpus.application.corpus import Corpus
from ebl.corpus.domain.line import Line
from ebl.corpus.domain.line_variant import LineVariant
from ebl.corpus.domain.lines_update import LinesUpdate
from ebl.corpus.domain.manuscript_line import ManuscriptLine
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.dictionary.domain.word import WordId
from ebl.errors import DataError
from ebl.tests.corpus.corpus_test_support import (
    CHAPTER,
    CHAPTER_WITHOUT_DOCUMENTS,
    UpdateDependencies,
    When,
    expect_bibliography,
    expect_find_and_update_chapter,
)
from ebl.tests.corpus.support import ANY_USER
from ebl.transliteration.domain.atf import ATF_PARSER_VERSION
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.normalized_akkadian import AkkadianWord
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import LanguageShift, ValueToken
from ebl.transliteration.domain.word_tokens import Word


def test_merging_lines(corpus: Corpus, update_dependencies: UpdateDependencies) -> None:
    reconstruction = (
        LanguageShift.normalized_akkadian(),
        AkkadianWord.of((ValueToken.of("buāru"),)),
    )
    is_second_line_of_parallelism = False
    is_beginning_of_section = False
    old_line_numbers = ()
    text_line = TextLine.of_iterable(
        LineNumber(1),
        (
            Word.of(
                [Reading.of_name("ku")], unique_lemma=(WordId("word1"),), alignment=0
            ),
            Word.of(
                [Reading.of_name("nu")], unique_lemma=(WordId("word2"),), alignment=1
            ),
        ),
    )
    manuscript_id = CHAPTER_WITHOUT_DOCUMENTS.manuscripts[0].id
    line = Line(
        LineNumber(1),
        (
            LineVariant(
                reconstruction,
                None,
                (ManuscriptLine(manuscript_id, (), text_line),),
            ),
        ),
        old_line_numbers,
        not is_second_line_of_parallelism,
        not is_beginning_of_section,
    )
    new_text_line = TextLine.of_iterable(
        LineNumber(1),
        (Word.of([Reading.of_name("ku")]), Word.of([Reading.of_name("ba")])),
    )
    new_line = Line(
        LineNumber(1),
        (
            LineVariant(
                reconstruction,
                None,
                (ManuscriptLine(manuscript_id, (), text_line.merge(new_text_line)),),
            ),
        ),
        old_line_numbers,
        is_second_line_of_parallelism,
        is_beginning_of_section,
    )
    old_chapter = attr.evolve(CHAPTER_WITHOUT_DOCUMENTS, lines=(line,))
    updated_chapter = attr.evolve(
        CHAPTER,
        lines=(new_line,),
        signs=("KU BA\nKU\nABZ075",),
        parser_version=ATF_PARSER_VERSION,
    )
    expect_find_and_update_chapter(update_dependencies, old_chapter, updated_chapter)

    assert (
        corpus.update_lines(
            CHAPTER.id_,
            LinesUpdate(
                [],
                set(),
                {
                    0: Line(
                        LineNumber(1),
                        (
                            LineVariant(
                                reconstruction,
                                None,
                                (ManuscriptLine(manuscript_id, (), new_text_line),),
                            ),
                        ),
                        old_line_numbers,
                        is_second_line_of_parallelism,
                        is_beginning_of_section,
                    )
                },
            ),
            update_dependencies.user,
        )
        == updated_chapter
    )


def test_update_lines_raises_exception_if_invalid_signs(
    corpus: Corpus,
    text_repository: MongoTextRepository,
    bibliography: Bibliography,
    when: When,
) -> None:
    lines = LinesUpdate([], set(), dict(enumerate(CHAPTER.lines)))
    when(text_repository).find_chapter(CHAPTER.id_).thenReturn(
        CHAPTER_WITHOUT_DOCUMENTS
    )
    expect_bibliography(bibliography, when)

    with pytest.raises(DataError):
        corpus.update_lines(CHAPTER.id_, lines, ANY_USER)
