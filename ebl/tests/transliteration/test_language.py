import pytest

from ebl.transliteration.domain.language import DEFAULT_LANGUAGE, Language


@pytest.mark.parametrize(
    "language,expected",
    [
        (Language.UNKNOWN, True),
        (Language.AKKADIAN, True),
        (Language.EMESAL, False),
        (Language.SUMERIAN, False),
        (Language.HITTITE, False),
    ],
)
def test_lemmatizable(language, expected):
    assert language.lemmatizable is expected


@pytest.mark.parametrize(
    "atf,expected",
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
        ("%e", Language.EMESAL),
        ("%n", Language.AKKADIAN),
        ("%akkgrc", Language.AKKADIAN),
        ("%suxgrc", Language.SUMERIAN),
        ("%grc", Language.GREEK),
        ("%hit", Language.HITTITE),
    ],
)
def test_of_atf(atf, expected):
    assert Language.of_atf(atf) == expected


def test_default_language():
    assert DEFAULT_LANGUAGE == Language.AKKADIAN
