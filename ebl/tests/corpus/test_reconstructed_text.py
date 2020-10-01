import pytest  # pyre-ignore[21]

from ebl.corpus.domain.reconstructed_text import (
    AkkadianWord,
    Caesura,
    Lacuna,
    MetricalFootSeparator,
    Modifier,
)
from ebl.transliteration.domain.enclosure_tokens import (
    BrokenAway,
    Emendation,
    PerhapsBrokenAway,
)
from ebl.transliteration.domain.tokens import Joiner, UnknownNumberOfSigns, ValueToken


@pytest.mark.parametrize(
    "word,expected",
    [
        (AkkadianWord.of((ValueToken.of("ibnû"),)), "ibnû"),
        (
            AkkadianWord.of(
                (ValueToken.of("ibnû"),),
                (Modifier.UNCERTAIN, Modifier.DAMAGED, Modifier.CORRECTED),
            ),
            "ibnû?#!",
        ),
        (AkkadianWord.of((BrokenAway.open(), ValueToken.of("ibnû"))), "[ibnû"),
        (
            AkkadianWord.of(
                (
                    BrokenAway.open(),
                    PerhapsBrokenAway.open(),
                    ValueToken.of("ib"),
                    PerhapsBrokenAway.close(),
                    ValueToken.of("nû"),
                    BrokenAway.close(),
                )
            ),
            "[(ib)nû]",
        ),
        (
            AkkadianWord.of(
                (
                    BrokenAway.open(),
                    PerhapsBrokenAway.open(),
                    Emendation.open(),
                    ValueToken.of("ib"),
                    PerhapsBrokenAway.close(),
                    ValueToken.of("nû"),
                    Emendation.close(),
                    BrokenAway.close(),
                )
            ),
            "[(<ib)nû>]",
        ),
        (
            AkkadianWord.of(
                (ValueToken.of("ibnû"), PerhapsBrokenAway.close(), BrokenAway.close()),
                (Modifier.UNCERTAIN,),
            ),
            "ibnû?)]",
        ),
        (
            AkkadianWord.of(
                (ValueToken.of("ib"), UnknownNumberOfSigns.of(), ValueToken.of("nû"))
            ),
            "ib...nû",
        ),
        (
            AkkadianWord.of(
                (ValueToken.of("ib"), Joiner.hyphen(), ValueToken.of("nû"))
            ),
            "ib-nû",
        ),
    ],
)
def test_akkadian_word(word, expected):
    assert str(word) == expected


@pytest.mark.parametrize(
    "lacuna,expected",
    [
        (Lacuna.of(tuple(), tuple()), "..."),
        (Lacuna.of((BrokenAway.open(),), tuple()), "[..."),
        (Lacuna.of(tuple(), (PerhapsBrokenAway.close(),)), "...)"),
        (
            Lacuna.of(
                (BrokenAway.open(), PerhapsBrokenAway.open()),
                (PerhapsBrokenAway.close(),),
            ),
            "[(...)",
        ),
    ],
)
def test_lacuna(lacuna, expected):
    assert str(lacuna) == expected


@pytest.mark.parametrize(
    "caesura,expected", [(Caesura.certain(), "||"), (Caesura.uncertain(), "(||)")]
)
def test_caesura(caesura, expected):
    assert str(caesura) == expected


@pytest.mark.parametrize(
    "separator,expected",
    [
        (MetricalFootSeparator.certain(), "|"),
        (MetricalFootSeparator.uncertain(), "(|)"),
    ],
)
def test_metrical_foot_separator(separator, expected):
    assert str(separator) == expected
