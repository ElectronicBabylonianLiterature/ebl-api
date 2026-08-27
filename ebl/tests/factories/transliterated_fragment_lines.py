from ebl.tests.factories.first_text_line import FIRST_TEXT_LINE
from ebl.tests.factories.fragment_text_words import (
    ba_ma_ti,
    broken_away_gap,
    broken_away_gap_end,
    broken_away_gap_start,
    damaged_unclear_sign,
    ki_du,
    mu,
    ta_ma_tu,
    u,
)
from ebl.transliteration.domain.enclosure_tokens import BrokenAway
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.sign_tokens import (
    Logogram,
    Reading,
)
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import (
    Joiner,
    ValueToken,
)
from ebl.transliteration.domain.word_tokens import Word


FIRST_TEXT_LINES = (
    FIRST_TEXT_LINE,
    TextLine.of_iterable(
        LineNumber(2, True),
        (
            Word.of(broken_away_gap()),
            Word.of([Logogram.of_name("GI", 6)]),
            Word.of([Reading.of_name("ana")]),
            Word.of(
                [
                    Reading.of_name("u", 4),
                    Joiner.hyphen(),
                    Reading.of(
                        (
                            ValueToken.of("š"),
                            BrokenAway.open(),
                            ValueToken.of("u"),
                        )
                    ),
                ]
            ),
            Word.of(broken_away_gap_end()),
        ),
    ),
    TextLine.of_iterable(
        LineNumber(3, True),
        (
            Word.of(broken_away_gap_start()),
            Word.of(ki_du()),
            Word.of(u()),
            Word.of(ba_ma_ti()),
            Word.of(broken_away_gap_end()),
        ),
    ),
    TextLine.of_iterable(
        LineNumber(6, True),
        (
            Word.of(broken_away_gap()),
            Word.of(damaged_unclear_sign()),
            Word.of(mu()),
            Word.of(ta_ma_tu()),
        ),
    ),
)
