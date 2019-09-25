import pytest

from ebl.transliteration.domain.language import DEFAULT_LANGUAGE, Language


def test_lemmatizable():
    assert Language.UNKNOWN.lemmatizable is True
    assert Language.AKKADIAN.lemmatizable is True
    assert Language.EMESAL.lemmatizable is False
    assert Language.SUMERIAN.lemmatizable is False


@pytest.mark.parametrize("atf,expected", [
    ('%ma', Language.AKKADIAN),
    ('%mb', Language.AKKADIAN),
    ('%na', Language.AKKADIAN),
    ('%nb', Language.AKKADIAN),
    ('%lb', Language.AKKADIAN),
    ('%sb', Language.AKKADIAN),
    ('%a', Language.AKKADIAN),
    ('%akk', Language.AKKADIAN),
    ('%eakk', Language.AKKADIAN),
    ('%oakk', Language.AKKADIAN),
    ('%ur3akk', Language.AKKADIAN),
    ('%oa', Language.AKKADIAN),
    ('%ob', Language.AKKADIAN),
    ('%sux', Language.SUMERIAN),
    ('%es', Language.EMESAL),
    ('%e', Language.EMESAL),
    ('%n', Language.AKKADIAN)
])
def test_of_atf(atf, expected):
    assert Language.of_atf(atf) == expected


def test_default_language():
    assert DEFAULT_LANGUAGE == Language.AKKADIAN
