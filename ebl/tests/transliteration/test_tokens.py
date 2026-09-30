import pytest

from ebl.lemmatization.domain.lemmatization import (
    LemmatizationError,
    LemmatizationToken,
)
from ebl.tests.asserts import assert_token_serialization
from ebl.transliteration.domain.alignment import AlignmentError, AlignmentToken
from ebl.transliteration.domain.enclosure_tokens import DocumentOrientedGloss
from ebl.transliteration.domain.enclosure_type import EnclosureType
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.tokens import (
    ErasureState,
    LanguageShift,
    UnknownNumberOfSigns,
    ValueToken,
)

TOKENS = [
    UnknownNumberOfSigns(frozenset({EnclosureType.BROKEN_AWAY}), ErasureState.NONE),
    LanguageShift.of("%sux"),
    DocumentOrientedGloss.open(),
]


def test_value_token():
    value = "value"
    token = ValueToken.of(value)
    equal = ValueToken.of(value)
    other = ValueToken.of("anothervalue")

    assert token.value == value
    assert token.clean_value == value
    assert token.get_key() == f"ValueToken⁝{value}"
    assert token.lemmatizable is False

    serialized = {"type": "ValueToken"}
    assert_token_serialization(token, serialized)

    assert token == equal
    assert hash(token) == hash(equal)

    assert token != other
    assert hash(token) != hash(other)


@pytest.mark.parametrize(
    "value,expected_language,normalized",
    [
        (r"%sux", Language.SUMERIAN, False),
        (r"%es", Language.EMESAL, False),
        (r"%sb", Language.AKKADIAN, False),
        (r"%n", Language.AKKADIAN, True),
        (r"%foo", Language.UNKNOWN, False),
    ],
)
def test_language_shift(value, expected_language, normalized):
    shift = LanguageShift.of(value)
    equal = LanguageShift.of(value)
    other = ValueToken.of(r"%bar")

    assert shift.value == value
    assert shift.clean_value == value
    assert shift.get_key() == f"LanguageShift⁝{value}"
    assert shift.lemmatizable is False
    assert shift.normalized == normalized
    assert shift.language == expected_language

    serialized = {
        "type": "LanguageShift",
        "normalized": normalized,
        "language": shift.language.name,
    }
    assert_token_serialization(shift, serialized)

    assert shift == equal
    assert hash(shift) == hash(equal)

    assert shift != other
    assert hash(shift) != hash(other)

    assert shift != ValueToken.of(value)


@pytest.mark.parametrize("token", TOKENS)
def test_set_unique_lemma_incompatible(token):
    lemma = LemmatizationToken("other-value")
    with pytest.raises(LemmatizationError):
        token.set_unique_lemma(lemma)


@pytest.mark.parametrize("token", TOKENS)
def test_set_unique_lemma_with_lemma(token):
    lemma = LemmatizationToken(token.value, ())
    with pytest.raises(LemmatizationError):
        token.set_unique_lemma(lemma)


@pytest.mark.parametrize("token", TOKENS)
def test_set_unique_lemma_no_lemma(token):
    lemma = LemmatizationToken(token.value)
    assert token.set_unique_lemma(lemma) == token


@pytest.mark.parametrize("token", TOKENS)
def test_set_alignment_incompatible(token):
    alignment = AlignmentToken("other-value", None)
    with pytest.raises(AlignmentError):
        alignment.apply(token)


@pytest.mark.parametrize("token", TOKENS)
def test_set_non_empty_alignment(token):
    alignment = AlignmentToken(token.value, 0)
    with pytest.raises(AlignmentError):
        alignment.apply(token)


@pytest.mark.parametrize("token", TOKENS)
def test_set_alignment_no_alignment(token):
    alignment = AlignmentToken(token.value, None)
    assert alignment.apply(token) == token


@pytest.mark.parametrize("old", TOKENS)
@pytest.mark.parametrize("new", TOKENS)
def test_merge(old, new):
    merged = old.merge(new)
    assert merged == new
