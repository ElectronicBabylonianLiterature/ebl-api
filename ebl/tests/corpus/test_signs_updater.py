from typing import List, Optional
import pytest
from ebl.corpus.application.schemas import ChapterSchema
from ebl.corpus.application.signs_updater import SignsUpdater
from ebl.corpus.domain.chapter import Chapter
from ebl.tests.factories.corpus import (
    ChapterFactory,
    LineFactory,
    LineVariantFactory,
    ManuscriptFactory,
    ManuscriptLineFactory,
)
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.word_tokens import Word
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.text import Text


def words_from_string(readings: str) -> List[Word]:
    return [Word.of([Reading.of_name(name)]) for name in readings.split()]


@pytest.fixture
def signs_updater(sign_repository):
    return SignsUpdater(sign_repository)


EMPTY_TEXT = Text([])
WORDS = ["ana ud", "ta ku mi", "šu ma"]
TEXTLINES = [
    TextLine.of_iterable(
        LineNumber(1),
        words_from_string("ši"),
    ),
]
MANUSCRIPTS = ManuscriptFactory.build_batch(
    3, colophon=EMPTY_TEXT, unplaced_lines=EMPTY_TEXT
)
VARIANT_WITH_EMPTY_MANUSCRIPT_TEXTLINE = LineVariantFactory.build(
    manuscripts=(
        ManuscriptLineFactory.build(
            manuscript_id=MANUSCRIPTS[0].id,
            line=TextLine.of_iterable(
                LineNumber(1),
                (Word.of([]),),
            ),
            labels=[],
        ),
    ),
)
VARIANTS = [
    [VARIANT_WITH_EMPTY_MANUSCRIPT_TEXTLINE],
    [
        LineVariantFactory.build(
            manuscripts=(
                ManuscriptLineFactory.build(
                    manuscript_id=MANUSCRIPTS[1].id,
                    line=TextLine.of_iterable(
                        LineNumber(i),
                        words_from_string(words),
                    ),
                    labels=[],
                ),
            ),
        )
        for i, words in enumerate(WORDS, start=2)
    ],
    [],
]
LINE_WITH_EMPTY_MANUSCRIPT_TEXTLINE = LineFactory.build(
    variants=[VARIANT_WITH_EMPTY_MANUSCRIPT_TEXTLINE]
)
LINE_WITHOUT_MANUSCRIPT_LINES = LineFactory.build(variants=[])
LINE_WITH_MANY_VARIANTS = LineFactory.build(variants=[])
LINES = [LineFactory.build(variants=variants) for variants in VARIANTS]


def update_and_serialize_signs(
    signs_updater: SignsUpdater, chapter: Chapter
) -> List[Optional[str]]:
    updated_chapter = signs_updater.update(chapter)
    return ChapterSchema().dump(updated_chapter)["signs"]


def test_empty_manuscript(signs_updater):
    chapter = ChapterFactory.build(
        manuscripts=MANUSCRIPTS, lines=[LINE_WITHOUT_MANUSCRIPT_LINES]
    )
    signs = update_and_serialize_signs(signs_updater, chapter)

    assert signs == [None for _ in MANUSCRIPTS]


def test_empty_textline(signs_updater):
    chapter = ChapterFactory.build(
        manuscripts=MANUSCRIPTS[:1], lines=[LINE_WITH_EMPTY_MANUSCRIPT_TEXTLINE]
    )
    signs = update_and_serialize_signs(signs_updater, chapter)

    assert signs == [""]


def test_sign_updater_completeness(signs_updater, signs, sign_repository):
    for sign in signs:
        sign_repository.create(sign)

    chapter = ChapterFactory.build(
        manuscripts=MANUSCRIPTS,
        lines=LINES,
    )
    signs = update_and_serialize_signs(signs_updater, chapter)

    assert signs == ["", "DIŠ UD\nTA KU MI\nŠU MA", None]
