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

CHAPTER_MERGE_CASES_1_1 = [
    (
        LineVariant(
            (AkkadianWord.of((ValueToken.of("buāru"),), has_variant_alignment=True),),
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
        LineVariant(
            (AkkadianWord.of((ValueToken.of("kurkur"),), has_variant_alignment=False),),
            manuscripts=(
                ManuscriptLine(
                    MANUSCRIPT_ID,
                    LABELS,
                    TextLine(
                        LineNumber(1),
                        (
                            Word.of(
                                [Reading.of_name("kur")],
                                alignment=None,
                                variant=None,
                            ),
                        ),
                    ),
                ),
            ),
        ),
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
