import pytest

from ebl.dictionary.domain.word import WordId
from ebl.lemmatization.domain.lemmatization import (
    LemmatizationError,
    LemmatizationToken,
)
from ebl.transliteration.domain.enclosure_tokens import (
    BrokenAway,
    Determinative,
    DocumentOrientedGloss,
    Erasure,
)
from ebl.transliteration.domain.enclosure_type import EnclosureType
from ebl.transliteration.domain.language import DEFAULT_LANGUAGE, Language
from ebl.transliteration.domain.lark_parser import parse_line
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.normalized_akkadian import AkkadianWord
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import (
    ErasureState,
    Joiner,
    LanguageShift,
    UnknownNumberOfSigns,
    ValueToken,
)
from ebl.transliteration.domain.word_tokens import LoneDeterminative, Word

LINE_NUMBER = LineNumber(1)


@pytest.mark.parametrize(
    "code,language",
    [
        ("%ma", Language.AKKADIAN),
        ("%mb", Language.AKKADIAN),
        ("%na", Language.AKKADIAN),
        ("%nb", Language.AKKADIAN),
        ("%lb", Language.AKKADIAN),
        ("%sb", Language.AKKADIAN),
        ("%a", Language.AKKADIAN),
        ("%akk", Language.AKKADIAN),
        ("%eakk", Language.AKKADIAN),
        ("%oakk", Language.AKKADIAN),
        ("%ur3akk", Language.AKKADIAN),
        ("%oa", Language.AKKADIAN),
        ("%ob", Language.AKKADIAN),
        ("%sux", Language.SUMERIAN),
        ("%es", Language.EMESAL),
        ("%hit", Language.HITTITE),
        ("%foo", DEFAULT_LANGUAGE),
    ],
)
def test_text_line_of_iterable(code: str, language: Language) -> None:
    tokens = [
        Word.of([Reading.of_name("first")]),
        LanguageShift.of(code),
        Word.of([Reading.of_name("second")]),
        LanguageShift.of("%sb"),
        LoneDeterminative.of([Determinative.of([Reading.of_name("third")])]),
        Word.of([BrokenAway.open(), Reading.of_name("fourth")]),
        UnknownNumberOfSigns.of(),
        BrokenAway.close(),
    ]
    expected_tokens = (
        Word.of([Reading.of_name("first")], DEFAULT_LANGUAGE),
        LanguageShift.of(code),
        Word.of([Reading.of_name("second")], language),
        LanguageShift.of("%sb"),
        LoneDeterminative.of(
            [Determinative.of([Reading.of_name("third")])], Language.AKKADIAN
        ),
        Word.of(
            [
                BrokenAway.open(),
                Reading.of(
                    (
                        ValueToken(
                            frozenset({EnclosureType.BROKEN_AWAY}),
                            ErasureState.NONE,
                            "fourth",
                        ),
                    )
                ).set_enclosure_type(frozenset({EnclosureType.BROKEN_AWAY})),
            ],
            DEFAULT_LANGUAGE,
        ),
        UnknownNumberOfSigns(frozenset({EnclosureType.BROKEN_AWAY}), ErasureState.NONE),
        BrokenAway.close().set_enclosure_type(frozenset({EnclosureType.BROKEN_AWAY})),
    )
    line = TextLine.of_iterable(LINE_NUMBER, tokens)

    assert line.line_number == LINE_NUMBER
    assert line.content == expected_tokens
    assert (
        line.key
        == f"TextLine⁞{line.atf}⟨{'⁚'.join(token.get_key() for token in expected_tokens)}⟩"
    )
    assert line.atf == f"1. first {code} second %sb {{third}} [fourth ...]"


def test_text_line_of_iterable_normalized() -> None:
    tokens = [
        LanguageShift.normalized_akkadian(),
        AkkadianWord.of((ValueToken.of("kur"),)),
    ]
    expected_tokens = (
        LanguageShift.normalized_akkadian(),
        AkkadianWord.of((ValueToken.of("kur"),)),
    )
    line = TextLine.of_iterable(LINE_NUMBER, tokens)

    assert line.content == expected_tokens
    assert (
        line.key
        == f"TextLine⁞{line.atf}⟨{'⁚'.join(token.get_key() for token in expected_tokens)}⟩"
    )

    assert line.atf == "1. %n kur"


@pytest.mark.parametrize(
    "atf",
    [
        "1. [{(he-pi₂ e]š-šu₂)}",
        "2. [he₂-<(pa₃)>]",
        "3. [{iti}...]",
        "4. [(x x x)]",
        "5. [...]-qa-[...]-ba-[...]",
        "6. [...+ku....] [....ku+...]",
        "7. [...] {bu} [...]",
        "8. [...]{bu} [...]",
        "9. [...] {bu}[...]",
        "10. [...]{bu}[...]",
        "11. in]-<(...)>",
        "12a. [ : ]",
        "12b. [ | ]",
        "13. [ %sux ]",
        "14. [ !cm ]",
        "15. ($___$) (x)-eš-am₃?#",
        "16. am₃ ($___$)",
        "17. pa {(he-pi₂)}",
        "18. du₃-am₃{{mu-un-<(du₃)>}}",
        "19. kur %n kur (||) kur %sux kur",
        "20. %n [...] (...) [(...)] <...>",
        "21. %n buāru (|) [... || ...]-buāru#]",
    ],
)
def test_text_line_atf(atf: str) -> None:
    line = parse_line(atf)
    assert line.atf == atf


def test_text_line_atf_gloss() -> None:
    line = TextLine.of_iterable(
        LINE_NUMBER,
        [
            DocumentOrientedGloss.open(),
            Word.of([Reading.of_name("mu")]),
            Word.of([Reading.of_name("bu")]),
            DocumentOrientedGloss.close(),
        ],
    )
    assert line.atf == f"{line.line_number.atf} {{(mu bu)}}"


@pytest.mark.parametrize(
    "erasure,expected",
    [
        ([Erasure.open(), Erasure.center(), Erasure.close()], "°\\°"),
        (
            [
                Erasure.open(),
                Word.of(
                    [Reading.of_name("mu"), Joiner.hyphen(), Reading.of_name("bu")]
                ),
                Erasure.center(),
                Erasure.close(),
            ],
            "°mu-bu\\°",
        ),
        (
            [
                Erasure.open(),
                Erasure.center(),
                Word.of(
                    [Reading.of_name("mu"), Joiner.hyphen(), Reading.of_name("bu")]
                ),
                Erasure.close(),
            ],
            "°\\mu-bu°",
        ),
        (
            [
                Erasure.open(),
                Word.of(
                    [Reading.of_name("mu"), Joiner.hyphen(), Reading.of_name("bu")]
                ),
                Erasure.center(),
                Word.of(
                    [Reading.of_name("mu"), Joiner.hyphen(), Reading.of_name("bu")]
                ),
                Erasure.close(),
            ],
            "°mu-bu\\mu-bu°",
        ),
    ],
)
def test_text_line_atf_erasure(erasure, expected: str) -> None:
    word = Word.of([Reading.of_name("mu"), Joiner.hyphen(), Reading.of_name("mu")])
    line = TextLine.of_iterable(LINE_NUMBER, [word, *erasure, word])
    assert line.atf == f"{line.line_number.atf} {word.value} {expected} {word.value}"


def test_lemmatization() -> None:
    line = TextLine.of_iterable(
        LINE_NUMBER,
        [
            Word.of([Reading.of_name("bu")], unique_lemma=(WordId("nu I"),)),
            UnknownNumberOfSigns.of(),
            Word.of([Reading.of_name("nu")]),
        ],
    )

    assert line.lemmatization == (
        LemmatizationToken("bu", (WordId("nu I"),)),
        LemmatizationToken("..."),
        LemmatizationToken("nu", tuple()),
    )


def test_update_lemmatization() -> None:
    line = TextLine.of_iterable(LINE_NUMBER, [Word.of([Reading.of_name("bu")])])
    lemmatization = (LemmatizationToken("bu", (WordId("nu I"),)),)
    expected = TextLine.of_iterable(
        LINE_NUMBER, [Word.of([Reading.of_name("bu")], unique_lemma=(WordId("nu I"),))]
    )

    assert line.update_lemmatization(lemmatization) == expected


def test_update_lemmatization_incompatible() -> None:
    line = TextLine.of_iterable(LINE_NUMBER, [Word.of([Reading.of_name("mu")])])
    lemmatization = (LemmatizationToken("bu", (WordId("nu I"),)),)
    with pytest.raises(LemmatizationError):  # pyre-ignore[16]
        line.update_lemmatization(lemmatization)


def test_update_lemmatization_wrong_lenght() -> None:
    line = TextLine.of_iterable(
        LINE_NUMBER,
        [Word.of([Reading.of_name("bu")]), Word.of([Reading.of_name("bu")])],
    )
    lemmatization = (LemmatizationToken("bu", (WordId("nu I"),)),)
    with pytest.raises(LemmatizationError):  # pyre-ignore[16]
        line.update_lemmatization(lemmatization)
