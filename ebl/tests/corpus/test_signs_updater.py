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


WORDS = ["ana ud", "ta ku mi", "šu ma"]


@pytest.fixture
def signs_updater(sign_repository, signs):
    for sign in signs:
        sign_repository.create(sign)
    return SignsUpdater(sign_repository)


@pytest.fixture
def empty_text():
    return Text([])


@pytest.fixture
def manuscripts(empty_text):
    return ManuscriptFactory.build_batch(
        3, colophon=empty_text, unplaced_lines=empty_text
    )


@pytest.fixture
def variant_with_empty_manuscript_textline(manuscripts):
    return LineVariantFactory.build(
        manuscripts=(
            ManuscriptLineFactory.build(
                manuscript_id=manuscripts[0].id,
                line=TextLine.of_iterable(
                    LineNumber(1),
                    (Word.of([]),),
                ),
                labels=[],
            ),
        ),
    )


@pytest.fixture
def variants(manuscripts, variant_with_empty_manuscript_textline):
    return [
        [variant_with_empty_manuscript_textline],
        [
            LineVariantFactory.build(
                manuscripts=(
                    ManuscriptLineFactory.build(
                        manuscript_id=manuscripts[1].id,
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


@pytest.fixture
def chapter_with_empty_manuscript_textline(
    manuscripts, variant_with_empty_manuscript_textline
):
    lines = [LineFactory.build(variants=[variant_with_empty_manuscript_textline])]
    return ChapterFactory.build(manuscripts=manuscripts[:1], lines=lines)


@pytest.fixture
def chapter_with_line_without_manuscript_line(manuscripts):
    return ChapterFactory.build(
        manuscripts=manuscripts, lines=[LineFactory.build(variants=[])]
    )


@pytest.fixture
def manuscript_with_colophon_lines(empty_text):
    return ManuscriptFactory.build(
        colophon=Text.of_iterable(
            [TextLine.of_iterable(LineNumber(100), words_from_string("ana bu"))]
        ),
        unplaced_lines=empty_text,
    )


@pytest.fixture
def manuscript_with_unplaced_lines(empty_text):
    return ManuscriptFactory.build(
        colophon=empty_text,
        unplaced_lines=Text.of_iterable(
            [TextLine.of_iterable(LineNumber(200), words_from_string("šu du"))]
        ),
    )


@pytest.fixture
def chapter_with_colophon_lines(manuscript_with_colophon_lines):
    return ChapterFactory.build(
        manuscripts=[manuscript_with_colophon_lines],
        lines=[LineFactory.build(variants=[])],
    )


@pytest.fixture
def chapter_with_unplaced_lines(manuscript_with_unplaced_lines):
    return ChapterFactory.build(
        manuscripts=[manuscript_with_unplaced_lines],
        lines=[LineFactory.build(variants=[])],
    )


@pytest.fixture
def complex_chapter(
    manuscripts,
    manuscript_with_colophon_lines,
    manuscript_with_unplaced_lines,
    variants,
):
    lines = [LineFactory.build(variants=subvariants) for subvariants in variants]
    return ChapterFactory.build(
        manuscripts=[
            *manuscripts,
            manuscript_with_colophon_lines,
            manuscript_with_unplaced_lines,
        ],
        lines=lines,
    )


def update_and_serialize_signs(
    signs_updater: SignsUpdater, chapter: Chapter
) -> List[Optional[str]]:
    updated_chapter = signs_updater.update(chapter)
    return ChapterSchema().dump(updated_chapter)["signs"]


def test_empty_manuscript(
    signs_updater, chapter_with_line_without_manuscript_line, manuscripts
):
    signs = update_and_serialize_signs(
        signs_updater, chapter_with_line_without_manuscript_line
    )

    assert signs == [None for _ in manuscripts]


def test_empty_textline(signs_updater, chapter_with_empty_manuscript_textline):
    signs = update_and_serialize_signs(
        signs_updater, chapter_with_empty_manuscript_textline
    )

    assert signs == [""]


def test_colophon_lines(signs_updater, chapter_with_colophon_lines):
    signs = update_and_serialize_signs(signs_updater, chapter_with_colophon_lines)

    assert signs == ["DIŠ BU"]


def test_unplaced_lines(signs_updater, chapter_with_unplaced_lines):
    signs = update_and_serialize_signs(signs_updater, chapter_with_unplaced_lines)

    assert signs == ["ŠU DU"]


def test_signs_updater_completeness(signs_updater, complex_chapter):
    signs = update_and_serialize_signs(signs_updater, complex_chapter)

    assert signs == ["", "DIŠ UD\nTA KU MI\nŠU MA", None, "DIŠ BU", "ŠU DU"]
