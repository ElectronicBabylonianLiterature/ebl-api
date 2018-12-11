import pytest
from ebl.fragmentarium.language import Language


def test_lemmatizable():
    assert Language.UNKNOWN.lemmatizable is True
    assert Language.AKKADIAN.lemmatizable is True
    assert Language.EMESAL.lemmatizable is False
    assert Language.SUMERIAN.lemmatizable is False


@pytest.mark.parametrize("atf,expected", [
    (r'%sux', Language.SUMERIAN),
    (r'%es', Language.EMESAL),
    (r'%sb', Language.AKKADIAN),
    (r'%foo', Language.UNKNOWN)
])
def test_of_atf(atf, expected):
    assert Language.of_atf(atf) == expected
