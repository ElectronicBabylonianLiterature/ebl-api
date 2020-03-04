import pytest

from ebl.tests.asserts import assert_token_serialization
from ebl.transliteration.application.token_schemas import dump_tokens
from ebl.transliteration.domain.enclosure_tokens import Determinative
from ebl.transliteration.domain.language import DEFAULT_LANGUAGE, Language
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.tokens import ValueToken
from ebl.transliteration.domain.word_tokens import (
    DEFAULT_NORMALIZED,
    ErasureState,
    LoneDeterminative,
)


def test_of_value():
    value = "{bu}"
    parts = [Determinative([Reading.of_name("bu")])]
    lone_determinative = LoneDeterminative.of_value(parts)
    assert lone_determinative.value == value
    assert lone_determinative.lemmatizable is False
    assert lone_determinative.language == DEFAULT_LANGUAGE
    assert lone_determinative.normalized is DEFAULT_NORMALIZED
    assert lone_determinative.unique_lemma == tuple()
    assert lone_determinative.erasure == ErasureState.NONE
    assert lone_determinative.alignment is None


@pytest.mark.parametrize(
    "language,normalized", [(Language.SUMERIAN, False), (Language.AKKADIAN, True),],
)
def test_lone_determinative(language, normalized):
    value = "{mu}"
    parts = [Determinative([Reading.of_name("mu")])]
    lone_determinative = LoneDeterminative(language, normalized, parts=parts)

    equal = LoneDeterminative(language, normalized, parts=parts)
    other_language = LoneDeterminative(Language.UNKNOWN, normalized, parts=parts)
    other_parts = LoneDeterminative(
        language, normalized, parts=[Determinative([Reading.of_name("bu")])]
    )
    other_normalized = LoneDeterminative(language, not normalized, parts=parts)

    assert lone_determinative.value == value
    assert lone_determinative.lemmatizable is False
    assert lone_determinative.language == language
    assert lone_determinative.normalized is normalized
    assert lone_determinative.unique_lemma == tuple()

    serialized = {
        "type": "LoneDeterminative",
        "value": lone_determinative.value,
        "uniqueLemma": [],
        "normalized": normalized,
        "language": lone_determinative.language.name,
        "lemmatizable": lone_determinative.lemmatizable,
        "erasure": ErasureState.NONE.name,
        "parts": dump_tokens(parts),
    }
    assert_token_serialization(lone_determinative, serialized)

    assert lone_determinative == equal
    assert hash(lone_determinative) == hash(equal)

    for not_equal in [
        other_language,
        other_parts,
        other_normalized,
    ]:
        assert lone_determinative != not_equal
        assert hash(lone_determinative) != hash(not_equal)

    assert lone_determinative != ValueToken(value)


def test_set_language():
    parts = [Determinative([Reading.of_name("bu")])]
    language = Language.SUMERIAN
    normalized = False
    lone_determinative = LoneDeterminative(
        Language.AKKADIAN, not normalized, parts=parts
    )
    expected = LoneDeterminative(language, normalized, parts=parts)

    assert lone_determinative.set_language(language, normalized) == expected
