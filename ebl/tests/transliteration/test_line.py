import pytest

from ebl.dictionary.domain.word import WordId
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.enclosure_tokens import (
    DocumentOrientedGloss,
    Erasure,
)
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
    TextLine,
    LooseDollarLine,
    ImageDollarLine,
    RulingDollarLine,
    StrictDollarLine,
    ScopeContainer,
)
from ebl.transliteration.domain.tokens import (
    LanguageShift,
    Tabulation,
    ValueToken,
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
def test_line_of_iterable(code, language, normalized):
    tokens = [
        Word("first"),
        LanguageShift(code),
        Word("second"),
        LanguageShift("%sb"),
        LoneDeterminative("{third}"),
    ]
    expected_tokens = (
        Word("first", DEFAULT_LANGUAGE, DEFAULT_NORMALIZED),
        LanguageShift(code),
        Word("second", language, normalized),
        LanguageShift("%sb"),
        LoneDeterminative("{third}", Language.AKKADIAN, False),
    )
    line = TextLine.of_iterable(LINE_NUMBER, tokens)

    assert line.prefix == LINE_NUMBER.to_atf()
    assert line.line_number == LINE_NUMBER
    assert line.content == expected_tokens
    assert line.key == "⁞".join(
        [str(line.atf)] + [token.get_key() for token in expected_tokens]
    )
    assert line.atf == f"1. first {code} second %sb {{third}}"


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
def test_text_line_atf(atf):
    line = parse_line(atf)
    assert line.atf == atf


@pytest.mark.parametrize(
    "word,token,expected",
    [
        (Word("mu-bu"), Tabulation("($___$)"), " mu-bu "),
        (Word("-mu-bu"), Tabulation("($___$)"), " -mu-bu "),
        (Word("mu-bu-"), Tabulation("($___$)"), " mu-bu- "),
        (Word("-mu-bu-"), Tabulation("($___$)"), " -mu-bu- "),
        (Word("-mu-bu-"), LanguageShift("%sux"), " -mu-bu- "),
    ],
)
def test_text_line_atf_partials(word, token, expected):
    line = TextLine.of_iterable(LINE_NUMBER, [token, word, token,])
    assert line.atf == f"{line.prefix} {token.value}{expected}{token.value}"


def test_text_line_atf_partial_start():
    word = Word("-mu")
    line = TextLine.of_iterable(LINE_NUMBER, [word])
    assert line.atf == f"{line.prefix} {word.value}"


def test_text_line_atf_gloss():
    line = TextLine.of_iterable(
        LINE_NUMBER,
        [
            DocumentOrientedGloss.open(),
            Word("mu"),
            Word("bu"),
            DocumentOrientedGloss.close(),
        ],
    )
    assert line.atf == f"{line.prefix} {{(mu bu)}}"


@pytest.mark.parametrize(
    "erasure,expected",
    [
        ([Erasure.open(), Erasure.center(), Erasure.close(),], "°\\°",),
        (
            [Erasure.open(), Word("mu-bu"), Erasure.center(), Erasure.close(),],
            "°mu-bu\\°",
        ),
        (
            [Erasure.open(), Erasure.center(), Word("mu-bu"), Erasure.close(),],
            "°\\mu-bu°",
        ),
        (
            [
                Erasure.open(),
                Word("mu-bu"),
                Erasure.center(),
                Word("mu-bu"),
                Erasure.close(),
            ],
            "°mu-bu\\mu-bu°",
        ),
    ],
)
def test_text_line_atf_erasure(word, erasure, expected):
    word = Word("mu-bu")
    line = TextLine.of_iterable(LINE_NUMBER, [word, *erasure, word])
    assert line.atf == f"{line.prefix} {word.value} {expected} {word.value}"


def test_control_line_of_single():
    prefix = "$"
    token = ValueToken("only")
    line = ControlLine.of_single(prefix, token)

    assert line == ControlLine("$", (token,))


def test_loose_dollar_line():
    expected = LooseDollarLine("end of side")

    assert expected.prefix == "$"
    assert expected.content == (ValueToken("(end of side)"),)
    assert expected.text == "end of side"


def test_image_dollar_line():
    expected = ImageDollarLine("1", "a", "great")

    assert expected.prefix == "$"
    assert expected.content == (ValueToken("(image 1a = great)"),)
    assert expected.number == "1"
    assert expected.letter == "a"
    assert expected.text == "great"


def test_ruling_dollar_line():
    expected = RulingDollarLine(atf.Ruling.DOUBLE)

    assert expected.prefix == "$"
    assert expected.content == (ValueToken("double ruling"),)
    assert expected.number == atf.Ruling.DOUBLE


def test_strict_dollar_line_with_none():
    scope = ScopeContainer(atf.Object.OBJECT, "what")
    expected = StrictDollarLine(None, atf.Extent.SEVERAL, scope, None, None)
    assert expected.prefix == "$"
    assert expected.scope.content == atf.Object.OBJECT
    assert expected.scope.text == "what"
    assert expected.content == (ValueToken("several object what"),)


def test_strict_dollar_line():
    expected = StrictDollarLine(
        atf.Qualification.AT_LEAST,
        atf.Extent.SEVERAL,
        ScopeContainer(atf.Scope.COLUMNS, ""),
        atf.State.BLANK,
        atf.Status.UNCERTAIN,
    )

    assert expected.prefix == "$"
    assert expected.qualification == atf.Qualification.AT_LEAST
    assert expected.scope.content == atf.Scope.COLUMNS
    assert expected.scope.text == ""
    assert expected.extent == atf.Extent.SEVERAL
    assert expected.state == atf.State.BLANK
    assert expected.status == atf.Status.UNCERTAIN
    assert expected.content == (ValueToken("at least several columns blank ?"),)


def test_strict_dollar_line_content():
    scope = ScopeContainer(atf.Surface.from_atf("obverse"))
    expected = StrictDollarLine(
        atf.Qualification("at least"), 1, scope, atf.State("blank"), atf.Status("?"),
    )

    assert expected.content == (ValueToken("at least 1 obverse blank ?"),)


@pytest.mark.parametrize(
    "line", [ControlLine.of_single("@", ValueToken("obverse")), EmptyLine()]
)
def test_update_lemmatization(line):
    lemmatization = tuple(LemmatizationToken(token.value) for token in line.content)
    assert line.update_lemmatization(lemmatization) == line


def test_update_lemmatization_text_line():
    line = TextLine.of_iterable(LINE_NUMBER, [Word("bu")])
    lemmatization = (LemmatizationToken("bu", (WordId("nu I"),)),)
    expected = TextLine.of_iterable(
        LINE_NUMBER, [Word("bu", unique_lemma=(WordId("nu I"),))]
    )

    assert line.update_lemmatization(lemmatization) == expected


def test_update_lemmatization_incompatible():
    line = TextLine.of_iterable(LINE_NUMBER, [Word("mu")])
    lemmatization = (LemmatizationToken("bu", (WordId("nu I"),)),)
    with pytest.raises(LemmatizationError):
        line.update_lemmatization(lemmatization)


def test_update_lemmatization_wrong_lenght():
    line = TextLine.of_iterable(LINE_NUMBER, [Word("bu"), Word("bu")])
    lemmatization = (LemmatizationToken("bu", (WordId("nu I"),)),)
    with pytest.raises(LemmatizationError):
        line.update_lemmatization(lemmatization)
