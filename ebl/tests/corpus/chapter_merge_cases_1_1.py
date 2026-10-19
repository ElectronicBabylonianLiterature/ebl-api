from ebl.corpus.domain.manuscript_line import ManuscriptLine
from ebl.corpus.domain.line_variant import LineVariant
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.normalized_akkadian import AkkadianWord
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import ValueToken
from ebl.transliteration.domain.word_tokens import Word
from ebl.tests.corpus.chapter_merge_fixtures import (
    LABELS,
    MANUSCRIPT_ID,
)


def _variant(word, has_variant_alignment, alignment, variant):
    return LineVariant(
        (
            AkkadianWord.of(
                (ValueToken.of(word),), has_variant_alignment=has_variant_alignment
            ),
        ),
        manuscripts=(
            ManuscriptLine(
                MANUSCRIPT_ID,
                LABELS,
                TextLine(
                    LineNumber(1),
                    (
                        Word.of(
                            [Reading.of_name("kur")],
                            alignment=alignment,
                            variant=variant,
                        ),
                    ),
                ),
            ),
        ),
    )


def aligned_variant(word):
    return _variant(word, True, 0, Word.of([Reading.of_name("kur")]))


def unaligned_variant(word):
    return _variant(word, False, None, None)


CHAPTER_MERGE_CASES_1_1 = [
    (
        aligned_variant("buāru"),
        unaligned_variant("kurkur"),
        LineVariant(
            (AkkadianWord.of((ValueToken.of("kurkur"),), has_variant_alignment=True),),
            manuscripts=(
                ManuscriptLine(
                    MANUSCRIPT_ID,
                    LABELS,
                    TextLine(
                        LineNumber(1),
                        (
                            Word.of(
                                [Reading.of_name("kur")],
                                alignment=0,
                                variant=Word.of([Reading.of_name("kur")]),
                            ),
                        ),
                    ),
                ),
            ),
        ),
    ),
]
