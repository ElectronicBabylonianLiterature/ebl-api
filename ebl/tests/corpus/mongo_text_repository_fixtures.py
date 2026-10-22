from ebl.corpus.application.schemas import ChapterSchema, TextSchema
from ebl.corpus.domain.text import Text
from ebl.dictionary.domain.word import WordId
from ebl.tests.factories.corpus import (
    ChapterFactory,
    LineFactory,
    LineVariantFactory,
    ManuscriptFactory,
    ManuscriptLineFactory,
    TextFactory,
    ChapterQueryColophonLinesFactory,
)
from ebl.transliteration.domain.genre import Genre
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.domain.normalized_akkadian import AkkadianWord
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import ValueToken
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
            references=(),
        ),
    ),
    lines=(
        LineFactory.build(manuscript_id=1, translation=TEXT.chapters[0].translation),
    ),
    uncertain_fragments=(),
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
            references=(),
        ),
    ),
    lines=(
        LineFactory.build(manuscript_id=1, translation=TEXT.chapters[0].translation),
    ),
    uncertain_fragments=(),
    is_filtered_query=True,
    colophon_lines_in_query=ChapterQueryColophonLinesFactory.build(
        colophon_lines_in_query={"1": [0]}
    ),
)
LEMMA_MANUSCRIPT = ManuscriptFactory.build()
QUERY_LEMMA = "qanû I"
CHAPTER_WITH_QUERY_LEMMA = ChapterFactory.build(
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
CHAPTER_WITH_MANUSCRIPT_LEMMA = ChapterFactory.build(
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
                        AkkadianWord.of((ValueToken.of("buāru"),), unique_lemma=()),
                    ),
                ),
            )
        ),
    ),
)

CHAPTER_SIGN_SCHEMA = ChapterSchema(
    only=["text_id", "stage", "name", "manuscripts", "signs"]
)


def when_text_in_collection(database, text=TEXT) -> None:
    database[TEXTS_COLLECTION].insert_one(TextSchema(exclude=["chapters"]).dump(text))


def when_chapter_in_collection(database, chapter=CHAPTER) -> None:
    database[CHAPTERS_COLLECTION].insert_one(ChapterSchema().dump(chapter))
