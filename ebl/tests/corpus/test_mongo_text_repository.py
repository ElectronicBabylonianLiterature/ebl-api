from typing import Sequence, Tuple
import attr
import pytest
from ebl.corpus.application.corpus import TextRepository

from ebl.corpus.application.schemas import ChapterSchema, TextSchema
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.chapter_display import ChapterDisplay
from ebl.corpus.domain.dictionary_line import DictionaryLine
from ebl.corpus.domain.text import Text, UncertainFragment
from ebl.dictionary.domain.word import WordId
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.normalized_akkadian import AkkadianWord
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.text_id import TextId
from ebl.errors import DuplicateError, NotFoundError
from ebl.fragmentarium.application.joins_schema import JoinSchema
from ebl.fragmentarium.domain.fragment import Fragment
from ebl.fragmentarium.domain.joins import Join, Joins
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.tests.factories.corpus import (
    ChapterFactory,
    LineFactory,
    LineVariantFactory,
    ManuscriptFactory,
    ManuscriptLineFactory,
    TextFactory,
    ChapterQueryColophonLinesFactory,
    ManuscriptAttestationFactory,
)
from ebl.tests.factories.fragment import FragmentFactory
from ebl.transliteration.domain.genre import Genre
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import ValueToken
from ebl.transliteration.domain.transliteration_query import TransliterationQuery
from ebl.transliteration.domain.word_tokens import Word


TEXTS_COLLECTION = "texts"
CHAPTERS_COLLECTION = "chapters"
JOINS_COLLECTION = "joins"
MANUSCRIPT_ID = 1
MUSEUM_NUMBER = MuseumNumber("X", "1")
UNCERTAIN_FRAGMENT = MuseumNumber("X", "2")
TEXT: Text = TextFactory.build()
LITERATURE_TEXT: Text = TextFactory.build(genre=Genre.LITERATURE)
CHAPTER = ChapterFactory.build(
    text_id=TEXT.id,
    stage=TEXT.chapters[0].stage,
    name=TEXT.chapters[0].name,
    manuscripts=(
        ManuscriptFactory.build(
            id=1,
            museum_number=MUSEUM_NUMBER,
            accession="",
            references=tuple(),
        ),
    ),
    lines=(
        LineFactory.build(manuscript_id=1, translation=TEXT.chapters[0].translation),
    ),
    uncertain_fragments=tuple(),
    is_filtered_query=False,
    colophon_lines_in_query=ChapterQueryColophonLinesFactory.build(),
)
CHAPTER_FILTERED_QUERY = ChapterFactory.build(
    text_id=TEXT.id,
    stage=TEXT.chapters[0].stage,
    name=TEXT.chapters[0].name,
    manuscripts=(
        ManuscriptFactory.build(
            id=1,
            museum_number=MUSEUM_NUMBER,
            accession="",
            references=tuple(),
        ),
    ),
    lines=(
        LineFactory.build(manuscript_id=1, translation=TEXT.chapters[0].translation),
    ),
    uncertain_fragments=tuple(),
    is_filtered_query=True,
    colophon_lines_in_query=ChapterQueryColophonLinesFactory.build(
        colophon_lines_in_query={"1": [0]}
    ),
)
LEMMA_MANUSCRIPT = ManuscriptFactory.build()
QUERY_LEMMA = "qanû I"
CHAPTER_WITH_QUERY_LEMMA: Chapter = ChapterFactory.build(
    text_id=LITERATURE_TEXT.id,
    manuscripts=(LEMMA_MANUSCRIPT,),
    lines=(
        LineFactory.build(
            variants=(
                LineVariantFactory.build(
                    manuscripts=(
                        ManuscriptLineFactory.build(manuscript_id=LEMMA_MANUSCRIPT.id),
                    ),
                    reconstruction=(
                        AkkadianWord.of(
                            (ValueToken.of("qane"),),
                            unique_lemma=(WordId(QUERY_LEMMA),),
                        ),
                    ),
                ),
            )
        ),
    ),
)
CHAPTER_WITH_MANUSCRIPT_LEMMA: Chapter = ChapterFactory.build(
    text_id=TEXT.id,
    manuscripts=(LEMMA_MANUSCRIPT,),
    lines=(
        LineFactory.build(
            variants=(
                LineVariantFactory.build(
                    manuscripts=(
                        ManuscriptLineFactory.build(
                            manuscript_id=LEMMA_MANUSCRIPT.id,
                            line=TextLine.of_iterable(
                                LineNumber(1),
                                [
                                    Word.of(
                                        [Reading.of_name("bu")],
                                        unique_lemma=(WordId(QUERY_LEMMA),),
                                    )
                                ],
                            ),
                        ),
                    ),
                    reconstruction=(
                        AkkadianWord.of(
                            (ValueToken.of("buāru"),), unique_lemma=tuple()
                        ),
                    ),
                ),
            )
        ),
    ),
)


def when_text_in_collection(database, text=TEXT) -> None:
    database[TEXTS_COLLECTION].insert_one(TextSchema(exclude=["chapters"]).dump(text))


def when_chapter_in_collection(database, chapter=CHAPTER) -> None:
    database[CHAPTERS_COLLECTION].insert_one(ChapterSchema().dump(chapter))


def test_creating_text(database, text_repository) -> None:
    text_repository.create(TEXT)

    inserted_text = database[TEXTS_COLLECTION].find_one(
        {"category": TEXT.category, "index": TEXT.index}, projection={"_id": False}
    )
    assert inserted_text == TextSchema(exclude=["chapters"]).dump(TEXT)


def test_creating_chapter(database, text_repository) -> None:
    text_repository.create_chapter(CHAPTER)

    inserted_chapter = database[CHAPTERS_COLLECTION].find_one(
        {
            "textId.category": CHAPTER.text_id.category,
            "textId.index": CHAPTER.text_id.index,
            "stage": CHAPTER.stage.value,
            "name": CHAPTER.name,
        },
        projection={"_id": False},
    )
    assert inserted_chapter == ChapterSchema().dump(CHAPTER)


def test_it_is_not_possible_to_create_duplicate_texts(text_repository) -> None:
    text_repository.create_indexes()
    text_repository.create(TEXT)

    with pytest.raises(DuplicateError):
        text_repository.create(TEXT)


def test_it_is_not_possible_to_create_duplicate_chapters(text_repository) -> None:
    text_repository.create_indexes()
    text_repository.create(CHAPTER)

    with pytest.raises(DuplicateError):
        text_repository.create(CHAPTER)


def test_finding_text(
    database, text_repository, bibliography_repository, fragment_repository
) -> None:
    text = attr.evolve(
        TEXT,
        chapters=(
            attr.evolve(
                TEXT.chapters[0],
                uncertain_fragments=(UncertainFragment(UNCERTAIN_FRAGMENT),),
            ),
        ),
    )
    chapter = attr.evolve(CHAPTER, uncertain_fragments=(UNCERTAIN_FRAGMENT,))
    when_text_in_collection(database, text)
    when_chapter_in_collection(database, chapter)
    fragment_repository.create(Fragment(UNCERTAIN_FRAGMENT))
    for reference in text.references:
        bibliography_repository.create(reference.document)

    assert text_repository.find(text.id) == text


def test_find_raises_exception_if_text_not_found(text_repository) -> None:
    with pytest.raises(NotFoundError):
        text_repository.find(TextId(Genre.LITERATURE, 1, 1))


def test_listing_texts(database, text_repository, bibliography_repository) -> None:
    another_text = attr.evolve(TEXT, index=2)
    another_chapter = attr.evolve(
        CHAPTER,
        text_id=another_text.id,
        stage=another_text.chapters[0].stage,
        name=another_text.chapters[0].name,
    )

    when_text_in_collection(database)
    when_text_in_collection(database, another_text)
    when_chapter_in_collection(database)
    when_chapter_in_collection(database, another_chapter)
    for reference in TEXT.references:
        bibliography_repository.create(reference.document)

    assert text_repository.list() == [TEXT, another_text]


def test_finding_chapter(database, text_repository) -> None:
    when_chapter_in_collection(database)

    assert text_repository.find_chapter(CHAPTER.id_) == CHAPTER


def test_finding_chapter_for_display(database, text_repository) -> None:
    when_text_in_collection(database)
    when_chapter_in_collection(database)

    assert text_repository.find_chapter_for_display(
        CHAPTER.id_
    ) == ChapterDisplay.of_chapter(TEXT, CHAPTER)


def test_finding_line(database, text_repository) -> None:
    when_chapter_in_collection(database)

    assert text_repository.find_line(CHAPTER.id_, 0) == CHAPTER.lines[0]


def test_finding_line_not_found(database, text_repository) -> None:
    when_chapter_in_collection(database)

    with pytest.raises(NotFoundError):
        text_repository.find_line(CHAPTER.id_, len(CHAPTER.lines))


def test_finding_line_chapter_not_found(database, text_repository) -> None:
    with pytest.raises(NotFoundError):
        text_repository.find_line(CHAPTER.id_, 0)


def test_updating_chapter(database, text_repository) -> None:
    updated_chapter = attr.evolve(
        CHAPTER, lines=tuple(), manuscripts=tuple(), signs=tuple()
    )
    when_chapter_in_collection(database)

    text_repository.update(CHAPTER.id_, updated_chapter)

    assert text_repository.find_chapter(CHAPTER.id_) == updated_chapter


def test_updating_non_existing_chapter_raises_exception(text_repository):
    with pytest.raises(NotFoundError):
        text_repository.update(CHAPTER.id_, CHAPTER)


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
        query=TransliterationQuery(string=string, sign_repository=sign_repository),
        pagination_index=0,
    )
    expected = [CHAPTER_FILTERED_QUERY] if is_match else []
    assert result == (expected, len(expected))


def make_dictionary_line(text: Text, chapter: Chapter) -> DictionaryLine:
    return DictionaryLine(
        text.id,
        text.name,
        chapter.name,
        chapter.lines[0],
    )


@pytest.mark.parametrize(
    "text,chapter,lemma_id,genre,expected",
    [
        (
            LITERATURE_TEXT,
            CHAPTER_WITH_QUERY_LEMMA,
            QUERY_LEMMA,
            None,
            ([make_dictionary_line(LITERATURE_TEXT, CHAPTER_WITH_QUERY_LEMMA)], 1),
        ),
        (
            TEXT,
            CHAPTER_WITH_QUERY_LEMMA,
            QUERY_LEMMA,
            Genre.DIVINATION,
            ([], 0),
        ),
        (
            TEXT,
            CHAPTER_WITH_MANUSCRIPT_LEMMA,
            QUERY_LEMMA,
            None,
            ([make_dictionary_line(TEXT, CHAPTER_WITH_MANUSCRIPT_LEMMA)], 1),
        ),
        (TEXT, CHAPTER, "definitely not a lemma", None, ([], 0)),
    ],
)
def test_query_by_lemma(
    text_repository: TextRepository,
    text: Text,
    chapter: Chapter,
    lemma_id: str,
    genre: Genre,
    expected: Tuple[Sequence[DictionaryLine], int],
) -> None:
    text_repository.create(text)
    text_repository.create_chapter(chapter)

    assert text_repository.query_by_lemma(lemma_id, 0, genre) == expected


def test_query_manuscripts_by_chapter(database, text_repository) -> None:
    when_chapter_in_collection(database)

    assert text_repository.query_manuscripts_by_chapter(CHAPTER.id_) == list(
        CHAPTER.manuscripts
    )


def test_query_manuscripts_by_chapter_not_found(database, text_repository) -> None:
    with pytest.raises(NotFoundError):
        assert text_repository.query_manuscripts_by_chapter(CHAPTER.id_)


def test_query_manuscripts_with_joins_by_chapter_no_joins(
    database, text_repository
) -> None:
    when_chapter_in_collection(database)

    assert text_repository.query_manuscripts_with_joins_by_chapter(CHAPTER.id_) == list(
        CHAPTER.manuscripts
    )


def test_query_manuscripts_with_joins_is_in_fragmentarium(
    database, text_repository, fragment_repository
) -> None:
    fragment_repository.create(FragmentFactory.build(number=MUSEUM_NUMBER))
    when_chapter_in_collection(database)

    assert text_repository.query_manuscripts_with_joins_by_chapter(CHAPTER.id_) == [
        attr.evolve(CHAPTER.manuscripts[0], is_in_fragmentarium=True)
    ]


def test_query_manuscripts_with_joins_by_chapter(database, text_repository) -> None:
    when_chapter_in_collection(database)
    join = Join(MUSEUM_NUMBER)
    database[JOINS_COLLECTION].insert_one(
        {
            "fragments": [
                {**JoinSchema(exclude=["is_in_fragmentarium"]).dump(join), "group": 0}
            ]
        }
    )

    assert text_repository.query_manuscripts_with_joins_by_chapter(CHAPTER.id_) == [
        attr.evolve(CHAPTER.manuscripts[0], joins=Joins(((join,),)))
    ]


def test_query_corpus_by_manuscript(database, text_repository) -> None:
    when_text_in_collection(database, text=attr.evolve(TEXT, references=()))
    when_chapter_in_collection(database)

    expected_manuscript_attestation = ManuscriptAttestationFactory.build(
        text=attr.evolve(TEXT, references=()),
        chapter_id=CHAPTER.id_,
        manuscript=CHAPTER.manuscripts[0],
    )

    assert text_repository.query_corpus_by_manuscript(
        [CHAPTER.manuscripts[0].museum_number]
    ) == [expected_manuscript_attestation]
