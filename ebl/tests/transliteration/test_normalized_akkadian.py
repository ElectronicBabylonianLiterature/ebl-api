from ebl.fragmentarium.application.named_entity_schema import NamedEntitySchema
import pytest

from ebl.dictionary.domain.word import WordId
from ebl.lemmatization.domain.lemmatization import LemmatizationToken
from ebl.tests.asserts import assert_token_serialization
from ebl.transliteration.application.token_schemas import OneOfTokenSchema
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


@pytest.mark.parametrize(
    "word,expected,lemmatizable",
    [
        (AkkadianWord.of((ValueToken.of("ibnû"),)), "ibnû", True),
        (
            AkkadianWord.of(
                (ValueToken.of("ibnû"),), (Flag.UNCERTAIN, Flag.DAMAGE, Flag.CORRECTION)
            ),
            "ibnû?#!",
            True,
        ),
        (AkkadianWord.of((BrokenAway.open(), ValueToken.of("ibnû"))), "[ibnû", True),
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
            True,
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
            True,
        ),
        (
            AkkadianWord.of(
                (ValueToken.of("ibnû"), PerhapsBrokenAway.close(), BrokenAway.close()),
                (Flag.UNCERTAIN,),
            ),
            "ibnû?)]",
            True,
        ),
        (
            AkkadianWord.of(
                (ValueToken.of("ib"), UnknownNumberOfSigns.of(), ValueToken.of("nû"))
            ),
            "ib...nû",
            False,
        ),
        (
            AkkadianWord.of(
                (ValueToken.of("ib"), Joiner.hyphen(), ValueToken.of("nû"))
            ),
            "ib-nû",
            True,
        ),
    ],
)
def test_akkadian_word(word: AkkadianWord, expected: str, lemmatizable: bool) -> None:
    assert word.value == expected
    assert word.clean_value == expected.translate(str.maketrans("", "", "[]()<>#?!"))
    assert word.lemmatizable is lemmatizable
    assert word.alignable is lemmatizable

    serialized = {
        "type": "AkkadianWord",
        "parts": OneOfTokenSchema().dump(word.parts, many=True),
        "modifiers": [modifier.value for modifier in word.modifiers],
        "uniqueLemma": [],
        "alignment": None,
        "variant": None,
        "lemmatizable": lemmatizable,
        "alignable": lemmatizable,
        "normalized": True,
        "language": "AKKADIAN",
        "hasVariantAlignment": word.has_variant_alignment,
        "hasOmittedAlignment": word.has_omitted_alignment,
        "id": word.id_,
        "namedEntities": NamedEntitySchema().dump(word.named_entities, many=True),
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
    lemma = LemmatizationToken("bu", ())
    expected = AkkadianWord.of((ValueToken.of("bu"),))

    assert word.set_unique_lemma(lemma) == expected


def test_set_alignment() -> None:
    word = AkkadianWord.of((ValueToken.of("bu"),))
    expected = AkkadianWord.of((ValueToken.of("bu"),), alignment=1)

    assert word.set_alignment(1, None) == expected


def test_set_alignment_empty() -> None:
    word = AkkadianWord.of((ValueToken.of("bu"),), alignment=1)
    expected = AkkadianWord.of((ValueToken.of("bu"),))

    assert word.set_alignment(None, None) == expected


@pytest.mark.parametrize(
    "caesura,is_uncertain,value",
    [(Caesura.certain(), False, "||"), (Caesura.uncertain(), True, "(||)")],
)
def test_caesura(caesura: Caesura, is_uncertain: bool, value: str) -> None:
    assert caesura.value == value
    assert caesura.is_uncertain == is_uncertain

    serialized = {"type": "Caesura", "isUncertain": is_uncertain}
    assert_token_serialization(caesura, serialized)


@pytest.mark.parametrize(
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

    serialized = {"type": "MetricalFootSeparator", "isUncertain": is_uncertain}
    assert_token_serialization(separator, serialized)
