from itertools import cycle
from typing import Iterator, List, Optional, Sequence, Tuple, TypeVar

import attr

from ebl.corpus.application.lemmatization import LineVariantLemmatization
from ebl.corpus.domain.alignment import ManuscriptLineAlignment
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.line import Line
from ebl.corpus.domain.line_variant import LineVariant
from ebl.corpus.domain.manuscript_line import ManuscriptLine
from ebl.dictionary.domain.word import WordId
from ebl.lemmatization.domain.lemmatization import Lemma, LemmatizationToken
from ebl.tests.corpus.line_move_support import (
    LINE_COUNT,
    MANUSCRIPT_IDS,
    create_move_chapter,
)
from ebl.tests.factories.corpus import (
    LineFactory,
    LineVariantFactory,
    ManuscriptLineFactory,
)
from ebl.transliteration.domain.alignment import AlignmentToken
from ebl.transliteration.domain.line import EmptyLine
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.normalized_akkadian import AkkadianWord, Caesura
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import (
    Joiner,
    LanguageShift,
    Tabulation,
    Token,
    UnknownNumberOfSigns,
    ValueToken,
)
from ebl.transliteration.domain.unknown_sign_tokens import UnclearSign
from ebl.transliteration.domain.word_tokens import AbstractWord, Word

T = TypeVar("T")
LineAlignments = Tuple[Tuple[ManuscriptLineAlignment, ...], ...]
LineLemmatizations = Tuple[LineVariantLemmatization, ...]
SPECIAL_INDEX = LINE_COUNT
ANNOTATION_LINE_COUNT = LINE_COUNT + 1
NEW_VARIANT: AbstractWord = Word.of([Reading.of_name("nu")])
NEW_ALIGNMENTS: Sequence[Tuple[int, Optional[AbstractWord]]] = (
    (3, NEW_VARIANT),
    (1, None),
)
NEW_OMITTED_WORDS: Sequence[int] = (1,)
NEW_RECONSTRUCTION_LEMMAS: Sequence[Lemma] = (
    (WordId("bēlu I"), WordId("bēlu II")),
    (),
)
NEW_MANUSCRIPT_LEMMAS: Sequence[Lemma] = ((), (WordId("šarru I"),))


def _create_special_line() -> Line:
    number = SPECIAL_INDEX + 1
    first_id, second_id = MANUSCRIPT_IDS
    text_line = TextLine.of_iterable(
        LineNumber(number),
        (
            Word.of([Reading.of_name("ku")]),
            Word.of([UnclearSign.of()]),
            Tabulation.of(),
        ),
    )
    return LineFactory.build(
        number=LineNumber(number),
        variants=(
            LineVariantFactory.build(
                reconstruction=(
                    LanguageShift.normalized_akkadian(),
                    AkkadianWord.of((ValueToken.of("buāru"),)),
                    Caesura.certain(),
                    AkkadianWord.of(
                        (
                            UnknownNumberOfSigns.of(),
                            Joiner.hyphen(),
                            ValueToken.of("buāru"),
                        )
                    ),
                ),
                manuscripts=(
                    ManuscriptLineFactory.build(manuscript_id=first_id, line=text_line),
                    ManuscriptLineFactory.build(
                        manuscript_id=second_id, line=EmptyLine(), omitted_words=()
                    ),
                ),
            ),
            LineVariantFactory.build(
                reconstruction=(
                    LanguageShift.normalized_akkadian(),
                    AkkadianWord.of((ValueToken.of("eliš"),)),
                ),
                manuscripts=(),
            ),
        ),
    ).set_variant_alignment_flags()


def create_annotation_chapter() -> Chapter:
    chapter = create_move_chapter()
    return attr.evolve(chapter, lines=(*chapter.lines, _create_special_line()))


def replace_item(items: Sequence[T], index: int, item: T) -> Tuple[T, ...]:
    return tuple(
        item if item_index == index else old_item
        for item_index, old_item in enumerate(items)
    )


def find_manuscript_lines(line: Line) -> List[ManuscriptLine]:
    return [
        manuscript_line
        for variant in line.variants
        for manuscript_line in variant.manuscripts
    ]


def _find_alignment_token(token: Token) -> AlignmentToken:
    return (
        AlignmentToken(token.value, token.alignment, token.variant)
        if isinstance(token, AbstractWord)
        else AlignmentToken(token.value, None)
    )


def find_line_alignment(line: Line) -> LineAlignments:
    return tuple(
        tuple(
            ManuscriptLineAlignment(
                tuple(map(_find_alignment_token, manuscript_line.get_line_content())),
                tuple(manuscript_line.omitted_words),
            )
            for manuscript_line in variant.manuscripts
        )
        for variant in line.variants
    )


def _create_new_manuscript_alignment(
    manuscript_line: ManuscriptLine,
) -> ManuscriptLineAlignment:
    alignments = iter(NEW_ALIGNMENTS)
    return ManuscriptLineAlignment(
        tuple(
            AlignmentToken(token.value, *next(alignments))
            if token.alignable
            else AlignmentToken(token.value, None)
            for token in manuscript_line.get_line_content()
        ),
        tuple(NEW_OMITTED_WORDS),
    )


def create_new_alignment(line: Line) -> LineAlignments:
    return tuple(
        tuple(map(_create_new_manuscript_alignment, variant.manuscripts))
        for variant in line.variants
    )


def _find_lemmatization(tokens: Sequence[Token]) -> Tuple[LemmatizationToken, ...]:
    return tuple(
        LemmatizationToken(token.value, token.unique_lemma)
        if isinstance(token, AbstractWord)
        else LemmatizationToken(token.value)
        for token in tokens
    )


def _find_variant_lemmatization(variant: LineVariant) -> LineVariantLemmatization:
    return LineVariantLemmatization(
        _find_lemmatization(variant.reconstruction),
        tuple(
            _find_lemmatization(manuscript_line.get_line_content())
            for manuscript_line in variant.manuscripts
        ),
    )


def find_line_lemmatization(line: Line) -> LineLemmatizations:
    return tuple(map(_find_variant_lemmatization, line.variants))


def _create_new_lemmatization(
    tokens: Sequence[Token], lemmas: Iterator[Lemma]
) -> Tuple[LemmatizationToken, ...]:
    return tuple(
        LemmatizationToken(token.value, next(lemmas))
        if token.lemmatizable
        else LemmatizationToken(token.value)
        for token in tokens
    )


def _create_new_variant_lemmatization(variant: LineVariant) -> LineVariantLemmatization:
    return LineVariantLemmatization(
        _create_new_lemmatization(
            variant.reconstruction, cycle(NEW_RECONSTRUCTION_LEMMAS)
        ),
        tuple(
            _create_new_lemmatization(
                manuscript_line.get_line_content(), cycle(NEW_MANUSCRIPT_LEMMAS)
            )
            for manuscript_line in variant.manuscripts
        ),
    )


def create_new_lemmatization(line: Line) -> LineLemmatizations:
    return tuple(map(_create_new_variant_lemmatization, line.variants))
