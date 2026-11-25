import attr
import pytest

from ebl.corpus.application.corpus import Corpus
from ebl.corpus.domain.chapter_display import ChapterDisplay
from ebl.corpus.domain.dictionary_line import DictionaryLine
from ebl.errors import Defect, NotFoundError
from ebl.tests.corpus.corpus_test_support import (
    CHAPTER,
    CHAPTER_WITHOUT_DOCUMENTS,
    TEXT,
    expect_bibliography,
)


def test_list_all_texts(text_repository) -> None:
    text_repository.create(TEXT)
    assert text_repository.list_all_texts() == [
        {"index": TEXT.index, "category": TEXT.category, "genre": TEXT.genre.value}
    ]


def test_list_all_chapters(text_repository) -> None:
    text_repository.create_chapter(CHAPTER)
    assert text_repository.list_all_chapters() == [
        {
            "chapter": CHAPTER.name,
            "stage": CHAPTER.stage.long_name,
            "index": CHAPTER.text_id.index,
            "category": CHAPTER.text_id.category,
            "genre": CHAPTER.text_id.genre.value,
        }
    ]


def test_find_text(corpus, text_repository, bibliography, when) -> None:
    when(text_repository).find(TEXT.id).thenReturn(TEXT)

    assert corpus.find(TEXT.id) == TEXT


def test_listing_texts(corpus, text_repository, when) -> None:
    when(text_repository).list().thenReturn([TEXT])

    assert corpus.list() == [TEXT]


def test_find_chapter(corpus, text_repository, bibliography, when) -> None:
    when(text_repository).find_chapter(CHAPTER.id_).thenReturn(
        CHAPTER_WITHOUT_DOCUMENTS
    )
    expect_bibliography(bibliography, when)

    assert corpus.find_chapter(CHAPTER.id_) == CHAPTER


def test_find_chapter_for_display(
    corpus, text_repository, parallel_line_injector, when
) -> None:
    chapter_display = ChapterDisplay.of_chapter(TEXT, CHAPTER)
    injected_chapter_display = attr.evolve(
        chapter_display,
        lines=tuple(
            attr.evolve(
                line,
                variants=tuple(
                    attr.evolve(
                        variant,
                        parallel_lines=parallel_line_injector.inject(
                            variant.parallel_lines
                        ),
                    )
                    for variant in line.variants
                ),
            )
            for line in chapter_display.lines
        ),
    )
    when(text_repository).find_chapter_for_display(CHAPTER.id_).thenReturn(
        chapter_display
    )

    assert corpus.find_chapter_for_display(CHAPTER.id_) == injected_chapter_display


def test_search_lemma(corpus: Corpus, text_repository, when) -> None:
    lemma = "testlemma I"
    dictionary_line = DictionaryLine(
        TEXT.id,
        TEXT.name,
        CHAPTER.name,
        CHAPTER.stage,
        CHAPTER.lines[0],
    )

    when(text_repository).query_by_lemma(lemma, None).thenReturn((dictionary_line,))

    assert corpus.search_lemma(lemma, None) == (dictionary_line,)


def test_find_line(corpus, text_repository, bibliography, when) -> None:
    number = 0
    when(text_repository).find_line(CHAPTER.id_, number).thenReturn(
        CHAPTER_WITHOUT_DOCUMENTS.lines[number]
    )
    when(text_repository).query_manuscripts_by_chapter(CHAPTER.id_).thenReturn(
        CHAPTER.manuscripts
    )
    expect_bibliography(bibliography, when)

    assert corpus.find_line(CHAPTER.id_, number) == (
        CHAPTER.lines[number],
        CHAPTER.manuscripts,
    )


def test_find_line_with_manuscript_joins(
    corpus, text_repository, bibliography, when
) -> None:
    expect_bibliography(bibliography, when)
    when(text_repository).query_manuscripts_with_joins_by_chapter(
        CHAPTER.id_
    ).thenReturn(CHAPTER.manuscripts)
    number = 0
    when(text_repository).find_line(CHAPTER.id_, number).thenReturn(
        CHAPTER_WITHOUT_DOCUMENTS.lines[number]
    )
    assert corpus.find_line_with_manuscript_joins(CHAPTER.id_, number) == (
        CHAPTER.lines[number],
        CHAPTER.manuscripts,
    )


def test_find_manuscripts(corpus, text_repository, bibliography, when) -> None:
    expect_bibliography(bibliography, when)
    when(text_repository).query_manuscripts_by_chapter(CHAPTER.id_).thenReturn(
        CHAPTER.manuscripts
    )

    assert corpus.find_manuscripts(CHAPTER.id_) == CHAPTER.manuscripts


def test_find_manuscripts_with_joins(
    corpus, text_repository, bibliography, when
) -> None:
    expect_bibliography(bibliography, when)
    when(text_repository).query_manuscripts_with_joins_by_chapter(
        CHAPTER.id_
    ).thenReturn(CHAPTER.manuscripts)

    assert corpus.find_manuscripts_with_joins(CHAPTER.id_) == CHAPTER.manuscripts


def test_find_chapter_raises_exception_if_references_not_found(
    corpus, text_repository, bibliography, when
) -> None:
    when(text_repository).find_chapter(CHAPTER.id_).thenReturn(
        CHAPTER_WITHOUT_DOCUMENTS
    )
    when(bibliography).find(...).thenRaise(NotFoundError())

    with pytest.raises(Defect):
        corpus.find_chapter(CHAPTER.id_)
