import json
from typing import List, Sequence, Tuple, TypeVar

import attr
import bson
from falcon import testing

from ebl.corpus.application.chapter_changelog import ChapterDiff
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.line import Line
from ebl.corpus.domain.line_move import LineMove
from ebl.corpus.domain.manuscript_line import ManuscriptLine
from ebl.dictionary.domain.word import WordId
from ebl.lemmatization.domain.lemmatization import Lemma
from ebl.tests.corpus.chapter_edit_support import ChapterEditRequest, post_edit
from ebl.tests.factories.corpus import (
    ChapterFactory,
    LineFactory,
    LineVariantFactory,
    ManuscriptFactory,
    ManuscriptLineFactory,
)
from ebl.tests.factories.parallel_line import (
    ParallelCompositionFactory,
    ParallelFragmentFactory,
    ParallelTextFactory,
)
from ebl.transliteration.domain.genre import Genre
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.markup import StringPart
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.domain.normalized_akkadian import AkkadianWord, Caesura
from ebl.transliteration.domain.note_line import NoteLine
from ebl.transliteration.domain.parallel_line import ParallelLine
from ebl.transliteration.domain.sign_tokens import Logogram, Reading
from ebl.transliteration.domain.text_id import TextId
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import LanguageShift, Token, ValueToken
from ebl.transliteration.domain.translation_line import Extent, TranslationLine
from ebl.transliteration.domain.word_tokens import AbstractWord, Word

T = TypeVar("T")
MOVE_SUFFIX = "/lines/move"
MOVE_QUERY = "view=outline&revision=legacy"
STORED_PARSER_VERSION = "0.0.1"
PARALLEL_TEXT_ID = TextId(Genre.LITERATURE, 1, 2)
MANUSCRIPT_IDS: Sequence[int] = (1, 2)
READINGS: Sequence[Tuple[str, str]] = (
    ("ku", "nu"),
    ("ana", "ud"),
    ("ta", "mi"),
    ("šu", "ma"),
)
LINE_SIGNS: Sequence[str] = ("KU ABZ075", "DIŠ UD", "TA MI", "ŠU MA")
MANUSCRIPT_SIGNS: Sequence[str] = ("KU", "ABZ075")
LINE_COUNT = len(READINGS)
LONG_LINE_COUNT = 30
LEMMA: Lemma = (WordId("aklu I"),)
OTHER_LEMMA: Lemma = (WordId("eliš I"),)
ALIGNED_INDEX = 1
OMITTED_INDEX = 3
MOVES: Sequence[LineMove] = tuple(
    LineMove(source, target)
    for source in range(LINE_COUNT)
    for target in range(LINE_COUNT)
    if source != target
)
MOVE = LineMove(0, 2)
SHORT_MOVE = LineMove(0, 1)
LONG_MOVE = LineMove(0, LONG_LINE_COUNT - 1)
EXTENT_KEEPING_MOVES: Sequence[LineMove] = (
    LineMove(2, 3),
    LineMove(2, 0),
    LineMove(3, 0),
)
INVALID_EXTENT = "Invalid extent 2 in line 1."
OVERLAPPING_EXTENTS = "Overlapping extents for language en."
EXTENT_BREAKING_MOVES: Sequence[Tuple[LineMove, str]] = (
    (LineMove(0, 1), INVALID_EXTENT),
    (LineMove(1, 0), INVALID_EXTENT),
    (LineMove(0, 3), INVALID_EXTENT),
    (LineMove(2, 1), OVERLAPPING_EXTENTS),
    (LineMove(3, 1), OVERLAPPING_EXTENTS),
)
UNCERTAIN_FRAGMENTS: Sequence[MuseumNumber] = (
    MuseumNumber.of("K.1"),
    MuseumNumber.of("BM.2.a"),
)


def reorder(items: Sequence[T], move: LineMove) -> Tuple[T, ...]:
    reordered = list(items)
    reordered.insert(move.target, reordered.pop(move.source))
    return tuple(reordered)


def invert(move: LineMove) -> LineMove:
    return LineMove(move.target, move.source)


def find_identities(lines: Sequence[Line]) -> List[int]:
    return [id(line) for line in lines]


def _find_for_number(items: Sequence[T], number: int) -> T:
    return items[(number - 1) % len(items)]


def create_signs(lines: Sequence[Line]) -> Tuple[str, ...]:
    rows = [_find_for_number(LINE_SIGNS, int(line.number.label)) for line in lines]
    return tuple("\n".join([*rows, *MANUSCRIPT_SIGNS]) for _ in MANUSCRIPT_IDS)


def _create_manuscript_line(
    manuscript_id: int, number: int, readings: Tuple[str, str]
) -> ManuscriptLine:
    aligned_reading, reading = readings
    return ManuscriptLineFactory.build(
        manuscript_id=manuscript_id,
        line=TextLine.of_iterable(
            LineNumber(number),
            (
                Word.of(
                    [Reading.of_name(aligned_reading)],
                    unique_lemma=LEMMA,
                    alignment=ALIGNED_INDEX,
                    variant=Word.of(
                        [Logogram.of_name("KU")], language=Language.SUMERIAN
                    ),
                ),
                Word.of([Reading.of_name(reading)], unique_lemma=OTHER_LEMMA),
            ),
        ),
        omitted_words=(OMITTED_INDEX,),
    )


def _create_parallel_lines() -> Tuple[ParallelLine, ...]:
    return (
        ParallelCompositionFactory.build(),
        ParallelTextFactory.build(text=PARALLEL_TEXT_ID),
        ParallelFragmentFactory.build(),
    )


def create_annotated_line(number: int, readings: Tuple[str, str]) -> Line:
    return LineFactory.build(
        number=LineNumber(number),
        translation=(
            TranslationLine((StringPart(f"translation {number}"),), "en", None),
        ),
        variant=LineVariantFactory.build(
            reconstruction=(
                LanguageShift.normalized_akkadian(),
                AkkadianWord.of((ValueToken.of("buāru"),), unique_lemma=LEMMA),
                Caesura.certain(),
                AkkadianWord.of((ValueToken.of("eliš"),), unique_lemma=OTHER_LEMMA),
            ),
            note=NoteLine((StringPart(f"note {number}"),)),
            manuscripts=tuple(
                _create_manuscript_line(manuscript_id, number, readings)
                for manuscript_id in MANUSCRIPT_IDS
            ),
            parallel_lines=_create_parallel_lines(),
        ),
    ).set_variant_alignment_flags()


def create_move_chapter(line_count: int = LINE_COUNT) -> Chapter:
    lines = tuple(
        create_annotated_line(number, _find_for_number(READINGS, number))
        for number in range(1, line_count + 1)
    )
    return ChapterFactory.build(
        manuscripts=tuple(
            ManuscriptFactory.build(
                id=manuscript_id, siglum_disambiguator=str(manuscript_id)
            )
            for manuscript_id in MANUSCRIPT_IDS
        ),
        lines=lines,
        signs=create_signs(lines),
        parser_version=STORED_PARSER_VERSION,
        uncertain_fragments=UNCERTAIN_FRAGMENTS,
    )


def create_extent_chapter() -> Chapter:
    chapter = create_move_chapter()
    extent = Extent(chapter.lines[1].number)
    first_line = attr.evolve(
        chapter.lines[0],
        translation=(TranslationLine((StringPart("extent"),), "en", extent),),
    )
    second_line = attr.evolve(chapter.lines[1], translation=())
    return attr.evolve(chapter, lines=(first_line, second_line, *chapter.lines[2:]))


def move_chapter_line(chapter: Chapter, move: LineMove) -> Chapter:
    lines = reorder(chapter.lines, move)
    return attr.evolve(chapter, lines=lines, signs=create_signs(lines))


def find_diff_size(diff: ChapterDiff) -> int:
    return len(bson.encode({"diff": diff}))


def find_words(tokens: Sequence[Token]) -> Sequence[AbstractWord]:
    return [token for token in tokens if isinstance(token, AbstractWord)]


def _assert_manuscript_line_is_annotated(manuscript_line: ManuscriptLine) -> None:
    words = find_words(manuscript_line.get_line_content())
    assert [word.alignment for word in words] == [ALIGNED_INDEX, None]
    assert [word.has_variant for word in words] == [True, False]
    assert [word.unique_lemma for word in words] == [LEMMA, OTHER_LEMMA]
    assert manuscript_line.omitted_words == (OMITTED_INDEX,)
    assert manuscript_line.labels
    assert manuscript_line.paratext


def assert_lines_are_annotated(lines: Sequence[Line]) -> None:
    variants = [variant for line in lines for variant in line.variants]
    assert len(variants) == LINE_COUNT
    for variant in variants:
        words = find_words(variant.reconstruction)
        assert [word.unique_lemma for word in words] == [LEMMA, OTHER_LEMMA]
        assert [word.has_variant_alignment for word in words] == [True, False]
        assert [word.has_omitted_alignment for word in words] == [False, True]
        assert variant.note is not None
        assert variant.parallel_lines
        assert tuple(variant.manuscript_ids) == tuple(MANUSCRIPT_IDS)
        for manuscript_line in variant.manuscripts:
            _assert_manuscript_line_is_annotated(manuscript_line)


def create_move_request(source: object, target: object) -> ChapterEditRequest:
    return ChapterEditRequest(MOVE_SUFFIX, json.dumps({"from": source, "to": target}))


def post_move(
    client: testing.TestClient, chapter: Chapter, move: LineMove, query_string: str
) -> testing.Result:
    return post_edit(
        client, chapter, create_move_request(move.source, move.target), query_string
    )
