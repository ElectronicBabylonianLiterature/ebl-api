import pytest

from ebl.dictionary.domain.word import WordId
from ebl.transliteration.domain.enclosure_tokens import (
    Determinative,
    DocumentOrientedGloss,
    Erasure,
    BrokenAway,
)
from ebl.transliteration.domain.enclosure_type import EnclosureType
from ebl.transliteration.domain.labels import LineNumberLabel
from ebl.transliteration.domain.language import DEFAULT_LANGUAGE, Language
from ebl.transliteration.domain.lark_parser import parse_line
from ebl.transliteration.domain.lemmatization import (
    LemmatizationError,
    LemmatizationToken,
)
from ebl.transliteration.domain.line import (
    ControlLine,
    EmptyLine,
)
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.tokens import (
    Joiner,
    LanguageShift,
    ValueToken,
    UnknownNumberOfSigns,
)
from ebl.transliteration.domain.word_tokens import (
    DEFAULT_NORMALIZED,
    LoneDeterminative,
    Word,
)

LINE_NUMBER = LineNumberLabel.from_atf("1.")


def test_empty_line():
    line = EmptyLine()

    assert line.prefix == ""
    assert line.content == tuple()
    assert line.key == ""
    assert line.atf == ""


@pytest.mark.parametrize(
    "code,language,normalized",
    [
        ("%ma", Language.AKKADIAN, False),
        ("%mb", Language.AKKADIAN, False),
        ("%na", Language.AKKADIAN, False),
        ("%nb", Language.AKKADIAN, False),
        ("%lb", Language.AKKADIAN, False),
        ("%sb", Language.AKKADIAN, False),
        ("%a", Language.AKKADIAN, False),
        ("%akk", Language.AKKADIAN, False),
        ("%eakk", Language.AKKADIAN, False),
        ("%oakk", Language.AKKADIAN, False),
        ("%ur3akk", Language.AKKADIAN, False),
        ("%oa", Language.AKKADIAN, False),
        ("%ob", Language.AKKADIAN, False),
        ("%sux", Language.SUMERIAN, False),
        ("%es", Language.EMESAL, False),
        ("%n", Language.AKKADIAN, True),
        ("%foo", DEFAULT_LANGUAGE, DEFAULT_NORMALIZED),
    ],
)
def test_line_of_iterable(code: str, language: Language, normalized: bool):
    tokens = [
        Word.of([Reading.of_name("first")]),
        LanguageShift.of(code),
        Word.of([Reading.of_name("second")]),
        LanguageShift.of("%sb"),
        LoneDeterminative.of([Determinative.of([Reading.of_name("third")])]),
        Word.of([BrokenAway.open(), Reading.of_name("fourth")]),
        UnknownNumberOfSigns(frozenset()),
        BrokenAway.close(),
    ]
    expected_tokens = (
        Word.of([Reading.of_name("first")], DEFAULT_LANGUAGE, DEFAULT_NORMALIZED),
        LanguageShift.of(code),
        Word.of([Reading.of_name("second")], language, normalized),
        LanguageShift.of("%sb"),
        LoneDeterminative.of(
            [Determinative.of([Reading.of_name("third")])], Language.AKKADIAN, False
        ),
        Word.of(
            [
                BrokenAway.open(),
                Reading.of(
                    (ValueToken(frozenset({EnclosureType.BROKEN_AWAY}), "fourth"),)
                ).set_enclosure_type(frozenset({EnclosureType.BROKEN_AWAY})),
            ],
            DEFAULT_LANGUAGE,
            DEFAULT_NORMALIZED,
        ),
        UnknownNumberOfSigns(frozenset({EnclosureType.BROKEN_AWAY})),
        BrokenAway.close().set_enclosure_type(frozenset({EnclosureType.BROKEN_AWAY})),
    )
    line = TextLine.of_iterable(LINE_NUMBER, tokens)

    assert line.prefix == LINE_NUMBER.to_atf()
    assert line.line_number == LINE_NUMBER
    assert line.content == expected_tokens
    assert line.key == "⁞".join(
        [str(line.atf)] + [token.get_key() for token in expected_tokens]
    )
    assert line.atf == f"1. first {code} second %sb {{third}} [fourth ...]"


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
        "12. [ : ]",
        "13. [ %sux ]",
        "14. [ !cm ]",
        "15. ($___$) -(x)-eš-am₃?#",
        "16. am₃- ($___$)",
        "17. pa- {(he-pi₂)}",
        "18. du₃-am₃{{mu-un-<(du₃)>}}",
    ],
)
def test_text_line_atf(atf: str):
    line = parse_line(atf)
    assert line.atf == atf


def test_text_line_atf_gloss():
    line = TextLine.of_iterable(
        LINE_NUMBER,
        [
            DocumentOrientedGloss.open(),
            Word.of([Reading.of_name("mu")]),
            Word.of([Reading.of_name("bu")]),
            DocumentOrientedGloss.close(),
        ],
    )
    assert line.atf == f"{line.prefix} {{(mu bu)}}"


@pytest.mark.parametrize(
    "erasure,expected",
    [
        ([Erasure.open(), Erasure.center(), Erasure.close(),], "°\\°",),
        (
            [
                Erasure.open(),
                Word.of(
                    [Reading.of_name("mu"), Joiner.hyphen(), Reading.of_name("bu"),]
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
                    [Reading.of_name("mu"), Joiner.hyphen(), Reading.of_name("bu"),]
                ),
                Erasure.close(),
            ],
            "°\\mu-bu°",
        ),
        (
            [
                Erasure.open(),
                Word.of(
                    [Reading.of_name("mu"), Joiner.hyphen(), Reading.of_name("bu"),]
                ),
                Erasure.center(),
                Word.of(
                    [Reading.of_name("mu"), Joiner.hyphen(), Reading.of_name("bu"),]
                ),
                Erasure.close(),
            ],
            "°mu-bu\\mu-bu°",
        ),
    ],
)
def test_text_line_atf_erasure(erasure, expected: str):
    word = Word.of([Reading.of_name("mu"), Joiner.hyphen(), Reading.of_name("mu")])
    line = TextLine.of_iterable(LINE_NUMBER, [word, *erasure, word])
    assert line.atf == f"{line.prefix} {word.value} {expected} {word.value}"


def test_control_line_of_single():
    prefix = "$"
    token = ValueToken.of("only")
    line = ControlLine.of_single(prefix, token)

    assert line == ControlLine("$", (token,))


@pytest.mark.parametrize(
    "line", [ControlLine.of_single("@", ValueToken.of("obverse")), EmptyLine()]
)
def test_update_lemmatization(line):
    lemmatization = tuple(LemmatizationToken(token.value) for token in line.content)
    assert line.update_lemmatization(lemmatization) == line


def test_update_lemmatization_text_line():
    line = TextLine.of_iterable(LINE_NUMBER, [Word.of([Reading.of_name("bu")])])
    lemmatization = (LemmatizationToken("bu", (WordId("nu I"),)),)
    expected = TextLine.of_iterable(
        LINE_NUMBER, [Word.of([Reading.of_name("bu")], unique_lemma=(WordId("nu I"),))],
    )

    assert line.update_lemmatization(lemmatization) == expected


def test_update_lemmatization_incompatible():
    line = TextLine.of_iterable(LINE_NUMBER, [Word.of([Reading.of_name("mu")])])
    lemmatization = (LemmatizationToken("bu", (WordId("nu I"),)),)
    with pytest.raises(LemmatizationError):
        line.update_lemmatization(lemmatization)


def test_update_lemmatization_wrong_lenght():
    line = TextLine.of_iterable(
        LINE_NUMBER,
        [Word.of([Reading.of_name("bu")]), Word.of([Reading.of_name("bu")])],
    )
    lemmatization = (LemmatizationToken("bu", (WordId("nu I"),)),)
    with pytest.raises(LemmatizationError):
        line.update_lemmatization(lemmatization)
