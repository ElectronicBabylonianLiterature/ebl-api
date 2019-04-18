import pytest

from ebl.text.language import Language
from ebl.text.lemmatization import LemmatizationError, LemmatizationToken
from ebl.text.token import (DEFAULT_NORMALIZED, DocumentOrientedGloss,
                            LanguageShift, LineContinuation, Side, Token)
from ebl.text.erasure import Erasure

TOKENS = [
    Token('...'),
    LanguageShift('%sux'),
    DocumentOrientedGloss('{(')
]


def test_token():
    value = 'value'
    token = Token(value)
    equal = Token(value)
    other = Token('anothervalue')

    assert token.value == value
    assert token.lemmatizable is False
    assert token.to_dict() == {
        'type': 'Token',
        'value': token.value
    }

    assert token == equal
    assert hash(token) == hash(equal)

    assert token != other
    assert hash(token) != hash(other)


@pytest.mark.parametrize("value,expected_language,normalized", [
    (r'%sux', Language.SUMERIAN, DEFAULT_NORMALIZED),
    (r'%es', Language.EMESAL, DEFAULT_NORMALIZED),
    (r'%sb', Language.AKKADIAN, DEFAULT_NORMALIZED),
    (r'%n', Language.AKKADIAN, True),
    (r'%foo', Language.UNKNOWN, DEFAULT_NORMALIZED)
])
def test_language_shift(value, expected_language, normalized):
    shift = LanguageShift(value)
    equal = LanguageShift(value)
    other = Token(r'%bar')

    assert shift.value == value
    assert shift.lemmatizable is False
    assert shift.normalized == normalized
    assert shift.language == expected_language
    assert shift.to_dict() == {
        'type': 'LanguageShift',
        'value': shift.value,
        'normalized': normalized,
        'language': shift.language.name
    }

    assert shift == equal
    assert hash(shift) == hash(equal)

    assert shift != other
    assert hash(shift) != hash(other)

    assert shift != Token(value)


def test_document_oriented_gloss():
    value = '{('
    gloss = DocumentOrientedGloss(value)
    equal = DocumentOrientedGloss(value)
    other = DocumentOrientedGloss(')}')

    assert gloss.value == value
    assert gloss.side == Side.LEFT
    assert gloss.lemmatizable is False
    assert gloss.to_dict() == {
        'type': 'DocumentOrientedGloss',
        'value': gloss.value
    }

    assert other.side == Side.RIGHT

    assert gloss == equal
    assert hash(gloss) == hash(equal)

    assert gloss != other
    assert hash(gloss) != hash(other)


@pytest.mark.parametrize("token", TOKENS)
def test_set_unique_lemma_incompatible(token):
    lemma = LemmatizationToken('other-value')
    with pytest.raises(LemmatizationError):
        token.set_unique_lemma(lemma)


@pytest.mark.parametrize("token", TOKENS)
def test_set_unique_lemma_with_lemma(token):
    lemma = LemmatizationToken(token.value, tuple())
    with pytest.raises(LemmatizationError):
        token.set_unique_lemma(lemma)


@pytest.mark.parametrize("token", TOKENS)
def test_set_unique_lemma_no_lemma(token):
    lemma = LemmatizationToken(token.value)
    assert token.set_unique_lemma(lemma) == token


def test_line_continuation():
    value = '→'
    continuation = LineContinuation(value)

    assert continuation.value == value
    assert continuation.lemmatizable is False
    assert continuation.to_dict() == {
        'type': 'LineContinuation',
        'value': continuation.value
    }


def test_erasure():
    value = '$(erasure)'
    erasure = Erasure(value)

    assert erasure.value == value
    assert erasure.lemmatizable is False
    assert erasure.to_dict() == {
        'type': 'Erasure',
        'value': erasure.value
    }
