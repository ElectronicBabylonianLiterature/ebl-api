from typing import List, Optional, Tuple

from ebl.fragmentarium.application.named_entity_schema import NamedEntitySchema
import pytest

from ebl.dictionary.domain.word import WordId
from ebl.lemmatization.domain.lemmatization import (
    LemmatizationError,
    LemmatizationToken,
)
from ebl.tests.asserts import assert_token_serialization
from ebl.transliteration.application.token_schemas import (
    OneOfTokenSchema,
    OneOfWordSchema,
)
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.enclosure_tokens import BrokenAway, PerhapsBrokenAway
from ebl.transliteration.domain.enclosure_tokens import Determinative, Erasure
from ebl.transliteration.domain.language import DEFAULT_LANGUAGE, Language
from ebl.transliteration.domain.sign_tokens import Logogram, Reading
from ebl.transliteration.domain.tokens import (
    Joiner,
    UnknownNumberOfSigns,
    ValueToken,
    Variant,
)
from ebl.transliteration.domain.unknown_sign_tokens import UnclearSign, UnidentifiedSign
from ebl.transliteration.domain.word_tokens import AbstractWord, ErasureState, Word

LEMMATIZABLE_TEST_WORDS: List[Tuple[Word, bool]] = [
    (Word.of([Reading.of_name("un")]), True),
    (Word.of([Reading.of_name("un")], language=Language.SUMERIAN), False),
    (Word.of([Reading.of_name("un")], language=Language.EMESAL), False),
    (Word.of([Reading.of_name("un"), Joiner.hyphen(), UnclearSign.of()]), False),
    (Word.of([UnidentifiedSign.of(), Joiner.hyphen(), Reading.of_name("un")]), False),
    (Word.of([Variant.of(Reading.of_name("un"), Reading.of_name("ia"))]), False),
    (
        Word.of([UnknownNumberOfSigns.of(), Joiner.hyphen(), Reading.of_name("un")]),
        False,
    ),
    (
        Word.of([Reading.of_name("un"), Joiner.hyphen(), UnknownNumberOfSigns.of()]),
        False,
    ),
    (
        Word.of(
            parts=[
                Reading.of_name("un"),
                Joiner.hyphen(),
                UnknownNumberOfSigns.of(),
                Joiner.hyphen(),
                Reading.of_name("un"),
            ]
        ),
        False,
    ),
]


def test_defaults() -> None:
    value = "value"
    reading = Reading.of_name(value)
    word = Word.of([reading])

    assert word.value == value
    assert word.clean_value == value
    assert word.get_key() == f"Word⁝{value}⟨{reading.get_key()}⟩"
    assert word.parts == (reading,)
    assert word.lemmatizable is True
    assert word.language == DEFAULT_LANGUAGE
    assert word.normalized is False
    assert word.unique_lemma == ()
    assert word.erasure == ErasureState.NONE
    assert word.alignment is None
    assert word.variant is None
    assert word.has_variant_alignment is False
    assert word.has_omitted_alignment is False


@pytest.mark.parametrize(
    "language,unique_lemma",
    [
        (Language.SUMERIAN, (WordId("ku II"), WordId("aklu I"))),
        (Language.EMESAL, ()),
        (Language.AKKADIAN, (WordId("aklu I"),)),
    ],
)
def test_word(language, unique_lemma) -> None:
    value = "ku"
    parts = [Reading.of_name("ku")]
    erasure = ErasureState.NONE
    variant = Word.of([Reading.of_name("ra")])
    alignment = 1
    word = Word.of(parts, language, unique_lemma, erasure, alignment, variant)

    expected_parts = f"⟨{'⁚'.join(part.get_key() for part in parts)}⟩" if parts else ""
    assert word.value == value
    assert word.clean_value == value
    assert word.get_key() == f"Word⁝{value}{expected_parts}"
    assert word.parts == tuple(parts)
    assert word.language == language
    assert word.normalized is False
    assert word.unique_lemma == unique_lemma
    assert word.alignment == alignment
    assert word.variant == variant

    serialized = {
        "type": "Word",
        "uniqueLemma": list(unique_lemma),
        "normalized": False,
        "language": word.language.name,
        "lemmatizable": word.lemmatizable,
        "alignable": word.lemmatizable,
        "erasure": erasure.name,
        "parts": OneOfTokenSchema().dump(parts, many=True),
        "alignment": 1,
        "variant": OneOfWordSchema().dump(variant),
        "hasVariantAlignment": word.has_variant_alignment,
        "hasOmittedAlignment": word.has_omitted_alignment,
        "namedEntities": NamedEntitySchema().dump(word.named_entities, many=True),
    }

    assert_token_serialization(word, serialized)


def test_clean_value() -> None:
    word = Word.of(
        [
            BrokenAway.open(),
            Erasure.open(),
            Reading.of_name("ra").set_erasure(ErasureState.ERASED),
            Erasure.center(),
            Reading.of(
                [ValueToken.of("ku"), BrokenAway.close(), ValueToken.of("r")]
            ).set_erasure(ErasureState.OVER_ERASED),
            Erasure.close(),
            Joiner.hyphen(),
            Variant.of(
                Reading.of([ValueToken.of("r"), BrokenAway.open(), ValueToken.of("a")]),
                Reading.of([ValueToken.of("p"), BrokenAway.open(), ValueToken.of("a")]),
            ),
            PerhapsBrokenAway.open(),
            Determinative.of(
                [
                    Logogram.of(
                        [ValueToken.of("KU"), BrokenAway.close(), ValueToken.of("R")]
                    )
                ]
            ),
            PerhapsBrokenAway.close(),
        ]
    )

    assert word.clean_value == "kur-ra/pa{KUR}"


@pytest.mark.parametrize("word,expected", LEMMATIZABLE_TEST_WORDS)
def test_lemmatizable(word, expected) -> None:
    assert word.lemmatizable == expected


@pytest.mark.parametrize("word,_", LEMMATIZABLE_TEST_WORDS)
def test_alignable(word, _) -> None:
    assert word.alignable == word.lemmatizable


@pytest.mark.parametrize(
    "variant,expected",
    [
        (Word.of([Reading.of_name("ra")]), True),
        (None, False),
    ],
)
def test_has_variant(variant: Optional[AbstractWord], expected: bool) -> None:
    assert Word.of([Reading.of_name("kur")], variant=variant).has_variant is expected


def test_set_language() -> None:
    unique_lemma = (WordId("aklu I"),)
    language = Language.SUMERIAN
    word = Word.of([Reading.of_name("kur")], Language.AKKADIAN, unique_lemma)
    expected_word = Word.of([Reading.of_name("kur")], language, unique_lemma)

    assert word.set_language(language) == expected_word


def test_set_unique_lemma() -> None:
    word = Word.of([Reading.of_name("bu")])
    lemma = LemmatizationToken("bu", (WordId("nu I"),))
    expected = Word.of([Reading.of_name("bu")], unique_lemma=(WordId("nu I"),))

    assert word.set_unique_lemma(lemma) == expected


def test_set_unique_lemma_empty() -> None:
    word = Word.of([Reading.of_name("bu")], Language.SUMERIAN)
    lemma = LemmatizationToken("bu", ())
    expected = Word.of([Reading.of_name("bu")], Language.SUMERIAN)

    assert word.set_unique_lemma(lemma) == expected


@pytest.mark.parametrize(
    "word",
    [
        Word.of([Reading.of_name("mu")]),
        Word.of(language=Language.SUMERIAN, parts=[Reading.of_name("bu")]),
        Word.of([Reading.of_name("bu"), Joiner.hyphen(), UnclearSign.of()]),
        Word.of([UnidentifiedSign.of(), Joiner.hyphen(), Reading.of_name("bu")]),
        Word.of([Variant.of(Reading.of_name("bu"), Reading.of_name("nu"))]),
        Word.of([Joiner.hyphen(), Reading.of_name("bu")]),
        Word.of([Reading.of_name("bu"), Joiner.hyphen()]),
    ],
)
def test_set_unique_lemma_invalid(word) -> None:
    lemma = LemmatizationToken("bu", (WordId("nu I"),))
    with pytest.raises(LemmatizationError):
        word.set_unique_lemma(lemma)


def test_set_alignment() -> None:
    word = Word.of([Reading.of_name("bu")])
    alignment = 1
    variant = Word.of([Reading.of_name("ra")])
    expected = Word.of([Reading.of_name("bu")], alignment=alignment, variant=variant)

    assert word.set_alignment(alignment, variant) == expected


@pytest.mark.parametrize(
    "old,new,expected",
    [
        (
            Word.of(alignment=1, parts=[Reading.of_name("bu")]),
            UnknownNumberOfSigns.of(),
            UnknownNumberOfSigns.of(),
        ),
        (
            Word.of(
                alignment=1,
                parts=[
                    BrokenAway.open(),
                    PerhapsBrokenAway.open(),
                    Reading.of_name("bu"),
                    PerhapsBrokenAway.close(),
                ],
            ),
            Word.of([Reading.of_name("bu")]),
            Word.of(alignment=1, parts=[Reading.of_name("bu")]),
        ),
        (
            Word.of(alignment=1, parts=[Reading.of_name("bu", flags=[*atf.Flag])]),
            Word.of([Reading.of_name("bu")]),
            Word.of(alignment=1, parts=[Reading.of_name("bu")]),
        ),
        (
            Word.of(alignment=1, parts=[Reading.of_name("bu")]),
            Word.of([Reading.of_name("bu", flags=[*atf.Flag])]),
            Word.of(alignment=1, parts=[Reading.of_name("bu", flags=[*atf.Flag])]),
        ),
        (
            Word.of(unique_lemma=(WordId("nu I"),), parts=[Reading.of_name("bu")]),
            Word.of(language=Language.SUMERIAN, parts=[Reading.of_name("bu")]),
            Word.of(language=Language.SUMERIAN, parts=[Reading.of_name("bu")]),
        ),
        (
            Word.of(alignment=1, parts=[Reading.of_name("bu")]),
            Word.of(language=Language.SUMERIAN, parts=[Reading.of_name("bu")]),
            Word.of(language=Language.SUMERIAN, parts=[Reading.of_name("bu")]),
        ),
        (
            Word.of(
                [
                    Variant.of(
                        Reading.of([ValueToken.of("k[ur")]),
                        Reading.of([ValueToken.of("r[a")]),
                    )
                ]
            ),
            Word.of(
                [
                    Variant.of(
                        Reading.of(
                            [ValueToken.of("k"), BrokenAway.open(), ValueToken.of("ur")]
                        ),
                        Reading.of(
                            [ValueToken.of("r"), BrokenAway.open(), ValueToken.of("a")]
                        ),
                    )
                ]
            ),
            Word.of(
                [
                    Variant.of(
                        Reading.of(
                            [ValueToken.of("k"), BrokenAway.open(), ValueToken.of("ur")]
                        ),
                        Reading.of(
                            [ValueToken.of("r"), BrokenAway.open(), ValueToken.of("a")]
                        ),
                    )
                ]
            ),
        ),
    ],
)
def test_merge(old, new: Word, expected: Word) -> None:
    assert old.merge(new) == expected
