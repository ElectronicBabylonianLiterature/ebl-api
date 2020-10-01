import pytest  # pyre-ignore[21]


from ebl.transliteration.domain.atf import Flag
from ebl.transliteration.domain.enclosure_tokens import (
    BrokenAway,
    Emendation,
    PerhapsBrokenAway,
)
from ebl.transliteration.domain.reconstructed_text import (
    AkkadianWord,
    Caesura,
    Lacuna,
    MetricalFootSeparator,
)
from ebl.transliteration.domain.tokens import Joiner, UnknownNumberOfSigns, ValueToken
from ebl.tests.asserts import assert_token_serialization
from ebl.transliteration.application.token_schemas import OneOfTokenSchema


@pytest.mark.parametrize(
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
def test_akkadian_word(word, expected):
    assert word.value == expected

    serialized = {
        "type": "AkkadianWord",
        "value": expected,
        "parts": OneOfTokenSchema(many=True).dump(word.parts),
        "modifiers": [modifier.value for modifier in word.modifiers],
        "enclosureType": [],
    }
    assert_token_serialization(word, serialized)


def test_akkadian_word_invalid_modifier():
    with pytest.raises(ValueError):
        AkkadianWord.of((ValueToken.of("ibnû"),), (Flag.COLLATION,))


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
    assert lacuna.value == expected

    token_schema = OneOfTokenSchema(many=True)
    serialized = {
        "type": "Lacuna",
        "value": expected,
        "before": token_schema.dump(lacuna.before),
        "after": token_schema.dump(lacuna.after),
        "enclosureType": [],
    }
    assert_token_serialization(lacuna, serialized)


@pytest.mark.parametrize(
    "caesura,is_uncertain,value",
    [(Caesura.certain(), False, "||"), (Caesura.uncertain(), True, "(||)")],
)
def test_caesura(caesura, is_uncertain, value):
    assert caesura.value == value
    assert caesura.is_uncertain == is_uncertain

    serialized = {
        "type": "Caesura",
        "value": value,
        "isUncertain": is_uncertain,
        "enclosureType": [],
    }
    assert_token_serialization(caesura, serialized)


@pytest.mark.parametrize(
    "separator,is_uncertain,value",
    [
        (MetricalFootSeparator.certain(), False, "|"),
        (MetricalFootSeparator.uncertain(), True, "(|)"),
    ],
)
def test_metrical_foot_separator(separator, is_uncertain, value):
    assert separator.value == value
    assert separator.is_uncertain == is_uncertain

    serialized = {
        "type": "MetricalFootSeparator",
        "value": value,
        "isUncertain": is_uncertain,
        "enclosureType": [],
    }
    assert_token_serialization(separator, serialized)
