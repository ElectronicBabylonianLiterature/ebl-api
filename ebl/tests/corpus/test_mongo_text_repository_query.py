from typing import Optional, Sequence, Tuple
import attr
import pytest

from ebl.corpus.application.text_repository import TextRepository
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.dictionary_line import DictionaryLine
from ebl.corpus.domain.text import Text
from ebl.tests.corpus.mongo_text_repository_fixtures import (
    CHAPTER,
    CHAPTER_FILTERED_QUERY,
    CHAPTER_WITH_MANUSCRIPT_LEMMA,
    CHAPTER_WITH_QUERY_LEMMA,
    LITERATURE_TEXT,
    QUERY_LEMMA,
    TEXT,
)
from ebl.transliteration.domain.genre import Genre
from ebl.transliteration.domain.text_id import TextId
from ebl.transliteration.domain.transliteration_query import TransliterationQuery
from ebl.transliteration.application.signs_visitor import SignsVisitor


@pytest.mark.parametrize(
    "string,is_match",
    [("KU", True), ("NU\nKU", True), ("UD", False)],
)
def test_query_by_transliteration(
    string, is_match, text_repository, sign_repository, signs
) -> None:
    for sign in signs:
        sign_repository.create(sign)
    text_repository.create_chapter(CHAPTER_FILTERED_QUERY)
    result = text_repository.query_by_transliteration(
        query=TransliterationQuery(
            string=string, visitor=SignsVisitor(sign_repository)
        ),
        pagination_index=0,
    )
    expected = [CHAPTER_FILTERED_QUERY] if is_match else []
    assert result == (expected, len(expected))


def make_dictionary_line(text: Text, chapter: Chapter, lemma: str) -> DictionaryLine:
    line = chapter.lines[0]
    return DictionaryLine(
        text.id,
        text.name,
        chapter.name,
        chapter.stage,
        attr.evolve(
            line,
            variants=tuple(
                attr.evolve(
                    variant,
                    manuscripts=tuple(
                        manuscript
                        for manuscript in variant.manuscripts
                        if manuscript.has_lemma(lemma)
                    ),
                )
                for variant in line.variants
            ),
        ),
        tuple(
            attr.evolve(
                manuscript,
                references=tuple(
                    attr.evolve(reference, document=None)
                    for reference in manuscript.references
                ),
            )
            for manuscript in chapter.manuscripts
        ),
    )


@pytest.mark.parametrize(
    "stored,query,expected",
    [
        (
            (LITERATURE_TEXT, CHAPTER_WITH_QUERY_LEMMA),
            (QUERY_LEMMA, None),
            [
                make_dictionary_line(
                    LITERATURE_TEXT, CHAPTER_WITH_QUERY_LEMMA, QUERY_LEMMA
                )
            ],
        ),
        (
            (TEXT, CHAPTER_WITH_QUERY_LEMMA),
            (QUERY_LEMMA, Genre.DIVINATION),
            [],
        ),
        (
            (TEXT, CHAPTER_WITH_MANUSCRIPT_LEMMA),
            (QUERY_LEMMA, None),
            [make_dictionary_line(TEXT, CHAPTER_WITH_MANUSCRIPT_LEMMA, QUERY_LEMMA)],
        ),
        ((TEXT, CHAPTER), ("definitely not a lemma", None), []),
    ],
)
def test_query_by_lemma(
    text_repository: TextRepository,
    stored: Tuple[Text, Chapter],
    query: Tuple[str, Optional[Genre]],
    expected: Sequence[DictionaryLine],
) -> None:
    text, chapter = stored
    lemma_id, genre = query
    text_repository.create(text)
    text_repository.create_chapter(chapter)

    assert text_repository.query_by_lemma(lemma_id, genre) == expected


def test_query_by_transliteration_lookup(
    text_repository, sign_repository, signs
) -> None:
    for sign in signs:
        sign_repository.create(sign)
    chapter = attr.evolve(
        CHAPTER_FILTERED_QUERY, text_id=TextId(TEXT.genre, TEXT.category, TEXT.index)
    )
    text_repository.create(TEXT)
    text_repository.create_chapter(chapter)
    result = text_repository.query_by_transliteration(
        TransliterationQuery(string="KU", visitor=SignsVisitor(sign_repository)), 0
    )
    expected = [attr.evolve(CHAPTER_FILTERED_QUERY, text_name=TEXT.name)]
    assert result == (expected, len(expected))
