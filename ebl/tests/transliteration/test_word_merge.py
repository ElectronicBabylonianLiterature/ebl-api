import pytest

from ebl.dictionary.domain.word import WordId
from ebl.lemmatization.domain.lemmatization import (
    LemmatizationError,
    LemmatizationToken,
)
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.enclosure_tokens import BrokenAway, PerhapsBrokenAway
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.tokens import (
    Joiner,
    UnknownNumberOfSigns,
    ValueToken,
    Variant,
)
from ebl.transliteration.domain.unknown_sign_tokens import UnclearSign, UnidentifiedSign
from ebl.transliteration.domain.word_tokens import Word


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
            Word.of(
                language=Language.SUMERIAN,
                parts=[Reading.of_name("bu")],
                unique_lemma=(WordId("nu I"),),
            ),
        ),
        (
            Word.of(alignment=1, parts=[Reading.of_name("bu")]),
            Word.of(language=Language.SUMERIAN, parts=[Reading.of_name("bu")]),
            Word.of(
                language=Language.SUMERIAN,
                parts=[Reading.of_name("bu")],
                alignment=1,
            ),
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
