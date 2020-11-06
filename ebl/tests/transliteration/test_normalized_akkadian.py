import pytest  # pyre-ignore[21]


from ebl.transliteration.domain.atf import Flag
from ebl.transliteration.domain.enclosure_tokens import (
    BrokenAway,
    Emendation,
    PerhapsBrokenAway,
)
from ebl.transliteration.domain.normalized_akkadian import (
    AkkadianWord,
    Caesura,
    MetricalFootSeparator,
)
from ebl.transliteration.domain.tokens import Joiner, UnknownNumberOfSigns, ValueToken
from ebl.tests.asserts import assert_token_serialization
from ebl.transliteration.application.token_schemas import OneOfTokenSchema
from ebl.transliteration.domain.alignment import AlignmentToken
from ebl.transliteration.domain.lemmatization import LemmatizationToken
from ebl.dictionary.domain.word import WordId


@pytest.mark.parametrize(  # pyre-ignore[56]
    "word,expected",
    [
        (AkkadianWord.of((ValueToken.of("ibnû"),)), "ibnû"),
        (
            AkkadianWord.of(
                (ValueToken.of("ibnû"),), (Flag.UNCERTAIN, Flag.DAMAGE, Flag.CORRECTION)
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
                (Flag.UNCERTAIN,),
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
def test_akkadian_word(word: AkkadianWord, expected: str) -> None:
    assert word.value == expected
    assert word.clean_value == expected.translate(str.maketrans("", "", "[]()<>#?!"))
    assert word.lemmatizable is True
    assert word.alignable is True

    serialized = {
        "type": "AkkadianWord",
        "value": expected,
        "parts": OneOfTokenSchema().dump(word.parts, many=True),  # pyre-ignore[16]
        "modifiers": [modifier.value for modifier in word.modifiers],
        "enclosureType": [],
        "uniqueLemma": [],
        "alignment": None,
    }
    assert_token_serialization(word, serialized)


def test_akkadian_word_invalid_modifier() -> None:
    with pytest.raises(ValueError):
        AkkadianWord.of((ValueToken.of("ibnû"),), (Flag.COLLATION,))


def test_set_unique_lemma() -> None:
    word = AkkadianWord.of((ValueToken.of("bu"),))
    lemma = LemmatizationToken("bu", (WordId("nu I"),))
    expected = AkkadianWord.of((ValueToken.of("bu"),), unique_lemma=(WordId("nu I"),))

    assert word.set_unique_lemma(lemma) == expected


def test_set_unique_lemma_empty() -> None:
    word = AkkadianWord.of((ValueToken.of("bu"),), unique_lemma=(WordId("nu I"),))
    lemma = LemmatizationToken("bu", tuple())
    expected = AkkadianWord.of((ValueToken.of("bu"),))

    assert word.set_unique_lemma(lemma) == expected


def test_set_alignment() -> None:
    word = AkkadianWord.of((ValueToken.of("bu"),))
    alignment = AlignmentToken("bu", 1)
    expected = AkkadianWord.of((ValueToken.of("bu"),), alignment=1)

    assert word.set_alignment(alignment) == expected


def test_set_alignment_empty() -> None:
    word = AkkadianWord.of((ValueToken.of("bu"),), alignment=1)
    alignment = AlignmentToken("bu", None)
    expected = AkkadianWord.of((ValueToken.of("bu"),))

    assert word.set_alignment(alignment) == expected


@pytest.mark.parametrize(  # pyre-ignore[56]
    "caesura,is_uncertain,value",
    [(Caesura.certain(), False, "||"), (Caesura.uncertain(), True, "(||)")],
)
def test_caesura(caesura: Caesura, is_uncertain: bool, value: str) -> None:
    assert caesura.value == value
    assert caesura.is_uncertain == is_uncertain

    serialized = {
        "type": "Caesura",
        "value": value,
        "isUncertain": is_uncertain,
        "enclosureType": [],
    }
    assert_token_serialization(caesura, serialized)


@pytest.mark.parametrize(  # pyre-ignore[56]
    "separator,is_uncertain,value",
    [
        (MetricalFootSeparator.certain(), False, "|"),
        (MetricalFootSeparator.uncertain(), True, "(|)"),
    ],
)
def test_metrical_foot_separator(
    separator: MetricalFootSeparator, is_uncertain: bool, value: str
) -> None:
    assert separator.value == value
    assert separator.is_uncertain == is_uncertain

    serialized = {
        "type": "MetricalFootSeparator",
        "value": value,
        "isUncertain": is_uncertain,
        "enclosureType": [],
    }
    assert_token_serialization(separator, serialized)
