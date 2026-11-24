from typing import Sequence, Tuple

import attr

from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.line import Line
from ebl.dictionary.domain.word import WordId
from ebl.lemmatization.domain.lemmatization import Lemma
from ebl.tests.corpus.line_move_support import (
    ALIGNED_INDEX,
    LEMMA,
    LINE_COUNT,
    MANUSCRIPT_IDS,
    OMITTED_INDEX,
    OTHER_LEMMA,
    create_move_chapter,
)
from ebl.tests.factories.corpus import (
    LineFactory,
    LineVariantFactory,
    ManuscriptLineFactory,
)
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.line import EmptyLine
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.normalized_akkadian import AkkadianWord, Caesura
from ebl.transliteration.domain.sign_tokens import Logogram, Reading
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import LanguageShift, ValueToken
from ebl.transliteration.domain.word_tokens import Word

CountCase = Tuple[str, int, int, Sequence[int]]
WORD = "ana"
MOVE_CHAPTER_WORD = "buāru"
NEW_LEMMA: Lemma = (WordId("ana I"), WordId("ana II"))
KEPT_LEMMA: Lemma = (WordId("anāku I"),)
VARIANTS_INDEX = LINE_COUNT
EMPTY_MANUSCRIPT_INDEX = VARIANTS_INDEX + 1
INSTANCES_LINE_COUNT = EMPTY_MANUSCRIPT_INDEX + 1
NO_INSTANCE_INDICES: Sequence[int] = (0, 2, 3)


@attr.s(frozen=True, auto_attribs=True)
class ReconstructionPosition:
    line: int
    variant: int
    token: int
    lemma: Lemma


@attr.s(frozen=True, auto_attribs=True)
class ManuscriptPosition:
    line: int
    variant: int
    manuscript: int
    token: int
    lemma: Lemma


RECONSTRUCTION_INSTANCES: Sequence[ReconstructionPosition] = (
    ReconstructionPosition(VARIANTS_INDEX, 0, 1, ()),
    ReconstructionPosition(VARIANTS_INDEX, 0, 3, NEW_LEMMA),
    ReconstructionPosition(VARIANTS_INDEX, 1, 1, OTHER_LEMMA),
    ReconstructionPosition(EMPTY_MANUSCRIPT_INDEX, 0, 1, ()),
)
MANUSCRIPT_INSTANCES: Sequence[ManuscriptPosition] = (
    ManuscriptPosition(1, 0, 0, 0, LEMMA),
    ManuscriptPosition(1, 0, 1, 0, LEMMA),
    ManuscriptPosition(VARIANTS_INDEX, 0, 0, 0, ()),
    ManuscriptPosition(VARIANTS_INDEX, 1, 0, 0, NEW_LEMMA),
)
NOT_LEMMATIZABLE_RECONSTRUCTION = ReconstructionPosition(VARIANTS_INDEX, 0, 4, ())
NOT_LEMMATIZABLE_MANUSCRIPT = ManuscriptPosition(VARIANTS_INDEX, 0, 0, 2, KEPT_LEMMA)
WORD_COUNT = 8
LEMMATIZED_COUNT = 5
INSTANCE_LINES: Sequence[int] = (1, VARIANTS_INDEX, EMPTY_MANUSCRIPT_INDEX)
WORDS_WITHOUT_INSTANCE: Sequence[str] = ("missing", "Ana", "an", "KU", "%hit", "||")
COUNT_CASES: Sequence[CountCase] = (
    (WORD, WORD_COUNT, LEMMATIZED_COUNT, INSTANCE_LINES),
    ("buāru", 4, 4, (0, 1, 2, 3)),
    ("eliš", 5, 4, (0, 1, 2, 3, EMPTY_MANUSCRIPT_INDEX)),
    ("ku", 2, 2, (0,)),
    ("ud", 3, 2, (1, VARIANTS_INDEX)),
    *((word, 0, 0, ()) for word in WORDS_WITHOUT_INSTANCE),
)


def _create_word(lemma: Lemma) -> Word:
    return Word.of(
        [Reading.of_name(WORD)],
        unique_lemma=lemma,
        alignment=ALIGNED_INDEX,
        variant=Word.of([Logogram.of_name("KU")], language=Language.SUMERIAN),
    )


def _create_reconstructed_word(value: str, lemma: Lemma) -> AkkadianWord:
    return AkkadianWord.of((ValueToken.of(value),), unique_lemma=lemma)


def _create_variants_line() -> Line:
    number = VARIANTS_INDEX + 1
    first_id, second_id = MANUSCRIPT_IDS
    return LineFactory.build(
        number=LineNumber(number),
        variants=(
            LineVariantFactory.build(
                reconstruction=(
                    LanguageShift.normalized_akkadian(),
                    _create_reconstructed_word(WORD, ()),
                    Caesura.certain(),
                    _create_reconstructed_word(WORD, NEW_LEMMA),
                    ValueToken.of(WORD),
                ),
                manuscripts=(
                    ManuscriptLineFactory.build(
                        manuscript_id=first_id,
                        line=TextLine.of_iterable(
                            LineNumber(number),
                            (
                                _create_word(()),
                                LanguageShift.of("%hit"),
                                Word.of(
                                    [Reading.of_name(WORD)], unique_lemma=KEPT_LEMMA
                                ),
                            ),
                        ),
                        omitted_words=(OMITTED_INDEX,),
                    ),
                ),
            ),
            LineVariantFactory.build(
                reconstruction=(
                    LanguageShift.normalized_akkadian(),
                    _create_reconstructed_word(WORD, OTHER_LEMMA),
                ),
                manuscripts=(
                    ManuscriptLineFactory.build(
                        manuscript_id=second_id,
                        line=TextLine.of_iterable(
                            LineNumber(number),
                            (_create_word(NEW_LEMMA), Word.of([Reading.of_name("ud")])),
                        ),
                        omitted_words=(),
                    ),
                ),
            ),
        ),
    ).set_variant_alignment_flags()


def _create_empty_manuscript_line() -> Line:
    return LineFactory.build(
        number=LineNumber(EMPTY_MANUSCRIPT_INDEX + 1),
        variants=(
            LineVariantFactory.build(
                reconstruction=(
                    LanguageShift.normalized_akkadian(),
                    _create_reconstructed_word(WORD, ()),
                    _create_reconstructed_word("eliš", ()),
                ),
                manuscripts=(
                    ManuscriptLineFactory.build(
                        manuscript_id=MANUSCRIPT_IDS[0],
                        line=EmptyLine(),
                        omitted_words=(),
                    ),
                ),
            ),
        ),
    ).set_variant_alignment_flags()


def create_instances_chapter() -> Chapter:
    chapter = create_move_chapter()
    return attr.evolve(
        chapter,
        lines=(
            *chapter.lines,
            _create_variants_line(),
            _create_empty_manuscript_line(),
        ),
    )
