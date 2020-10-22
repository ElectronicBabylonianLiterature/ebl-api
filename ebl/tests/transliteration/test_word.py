from typing import List, Tuple

import pytest  # pyre-ignore

from ebl.dictionary.domain.word import WordId
from ebl.tests.asserts import assert_token_serialization
from ebl.transliteration.application.token_schemas import OneOfTokenSchema
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.alignment import AlignmentError, AlignmentToken
from ebl.transliteration.domain.enclosure_tokens import BrokenAway, PerhapsBrokenAway
from ebl.transliteration.domain.language import DEFAULT_LANGUAGE, Language
from ebl.transliteration.domain.lemmatization import (
    LemmatizationError,
    LemmatizationToken,
)
from ebl.transliteration.domain.sign_tokens import Logogram, Reading
from ebl.transliteration.domain.unknown_sign_tokens import UnclearSign, UnidentifiedSign
from ebl.transliteration.domain.enclosure_tokens import Determinative, Erasure
from ebl.transliteration.domain.tokens import (
    Joiner,
    UnknownNumberOfSigns,
    ValueToken,
    Variant,
)
from ebl.transliteration.domain.word_tokens import (
    DEFAULT_NORMALIZED,
    ErasureState,
    Word,
)

LEMMATIZABLE_TEST_WORDS: List[Tuple[Word, bool]] = [
    (Word.of([Reading.of_name("un")]), True),
    (Word.of([Reading.of_name("un")], normalized=True), False),
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


def test_default_normalized() -> None:
    assert DEFAULT_NORMALIZED is False


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
    assert word.normalized is DEFAULT_NORMALIZED
    assert word.unique_lemma == tuple()
    assert word.erasure == ErasureState.NONE
    assert word.alignment is None


@pytest.mark.parametrize(  # pyre-ignore[56]
    "language,normalized,unique_lemma",
    [
        (Language.SUMERIAN, False, (WordId("ku II"), WordId("aklu I"))),
        (Language.SUMERIAN, True, tuple()),
        (Language.EMESAL, False, tuple()),
        (Language.EMESAL, True, tuple()),
        (Language.AKKADIAN, False, (WordId("aklu I"),)),
        (Language.AKKADIAN, True, tuple()),
    ],
)
def test_word(language, normalized, unique_lemma) -> None:
    value = "ku"
    parts = [Reading.of_name("ku")]
    erasure = ErasureState.NONE
    word = Word.of(parts, language, normalized, unique_lemma, erasure)

    equal = Word.of(parts, language, normalized, unique_lemma)
    other_language = Word.of(parts, Language.UNKNOWN, normalized, unique_lemma)
    other_parts = Word.of([Reading.of_name("nu")], language, normalized, unique_lemma)
    other_unique_lemma = Word.of(parts, language, normalized, (WordId("waklu I"),))
    other_normalized = Word.of(parts, language, not normalized, unique_lemma)
    other_erasure = Word.of(
        parts, language, normalized, unique_lemma, ErasureState.ERASED
    )
    expected_parts = f"⟨{'⁚'.join(part.get_key() for part in parts)}⟩" if parts else ""
    assert word.value == value
    assert word.clean_value == value
    assert word.get_key() == f"Word⁝{value}{expected_parts}"
    assert word.parts == tuple(parts)
    assert word.language == language
    assert word.normalized is normalized
    assert word.unique_lemma == unique_lemma

    serialized = {
        "type": "Word",
        "value": word.value,
        "uniqueLemma": [*unique_lemma],
        "normalized": normalized,
        "language": word.language.name,
        "lemmatizable": word.lemmatizable,
        "erasure": erasure.name,
        "parts": OneOfTokenSchema().dump(parts, many=True),  # pyre-ignore[16]
        "enclosureType": [type.name for type in word.enclosure_type],
    }
    assert_token_serialization(word, serialized)

    assert word == equal
    assert hash(word) == hash(equal)

    for not_equal in [
        other_language,
        other_parts,
        other_unique_lemma,
        other_normalized,
        other_erasure,
    ]:
        assert word != not_equal
        assert hash(word) != hash(not_equal)

    assert word != ValueToken.of(value)


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


@pytest.mark.parametrize("word,expected", LEMMATIZABLE_TEST_WORDS)  # pyre-ignore[56]
def test_lemmatizable(word, expected) -> None:
    assert word.lemmatizable == expected


@pytest.mark.parametrize("word,_", LEMMATIZABLE_TEST_WORDS)  # pyre-ignore[56]
def test_alignable(word, _) -> None:
    assert word.alignable == word.lemmatizable


def test_set_language() -> None:
    unique_lemma = (WordId("aklu I"),)
    language = Language.SUMERIAN
    normalized = False
    word = Word.of(
        [Reading.of_name("kur")], Language.AKKADIAN, not normalized, unique_lemma
    )
    expected_word = Word.of(
        [Reading.of_name("kur")], language, normalized, unique_lemma
    )

    assert word.set_language(language, normalized) == expected_word


def test_set_unique_lemma() -> None:
    word = Word.of([Reading.of_name("bu")])
    lemma = LemmatizationToken("bu", (WordId("nu I"),))
    expected = Word.of([Reading.of_name("bu")], unique_lemma=(WordId("nu I"),))

    assert word.set_unique_lemma(lemma) == expected


def test_set_unique_lemma_empty() -> None:
    word = Word.of([Reading.of_name("bu")], Language.SUMERIAN)
    lemma = LemmatizationToken("bu", tuple())
    expected = Word.of([Reading.of_name("bu")], Language.SUMERIAN)

    assert word.set_unique_lemma(lemma) == expected


@pytest.mark.parametrize(  # pyre-ignore[56]
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
    alignment = AlignmentToken("bu", 1)
    expected = Word.of([Reading.of_name("bu")], alignment=1)

    assert word.set_alignment(alignment) == expected


def test_set_alignment_empty() -> None:
    word = Word.of([Reading.of_name("bu")], Language.SUMERIAN)
    alignment = AlignmentToken("bu", None)
    expected = Word.of([Reading.of_name("bu")], Language.SUMERIAN)

    assert word.set_alignment(alignment) == expected


@pytest.mark.parametrize(  # pyre-ignore[56]
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
def test_set_alignment_invalid(word) -> None:
    alignment = AlignmentToken("bu", 0)
    with pytest.raises(AlignmentError):
        word.set_alignment(alignment)


@pytest.mark.parametrize(  # pyre-ignore[56]
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
def test_merge(old, new, expected) -> None:
    assert old.merge(new) == expected
