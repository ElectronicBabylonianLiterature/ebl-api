import pytest

from ebl.tests.asserts import assert_token_serialization
from ebl.transliteration.application.token_schemas import OneOfTokenSchema
from ebl.transliteration.domain.enclosure_tokens import Determinative
from ebl.transliteration.domain.language import DEFAULT_LANGUAGE, Language
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.tokens import ValueToken
from ebl.transliteration.domain.word_tokens import ErasureState, LoneDeterminative


def test_of_value():
    value = "{bu}"
    parts = [Determinative.of([Reading.of_name("bu")])]
    lone_determinative = LoneDeterminative.of_value(parts)
    assert lone_determinative.value == value
    assert lone_determinative.lemmatizable is False
    assert lone_determinative.language == DEFAULT_LANGUAGE
    assert lone_determinative.normalized is False
    assert lone_determinative.unique_lemma == ()
    assert lone_determinative.erasure == ErasureState.NONE
    assert lone_determinative.alignment is None


@pytest.mark.parametrize("language", [Language.SUMERIAN, Language.AKKADIAN])
def test_lone_determinative(language):
    value = "{mu}"
    parts = [Determinative.of([Reading.of_name("mu")])]
    lone_determinative = LoneDeterminative.of(parts, language)

    equal = LoneDeterminative.of(parts, language)
    other_language = LoneDeterminative.of(parts, Language.UNKNOWN)
    other_parts = LoneDeterminative.of(
        [Determinative.of([Reading.of_name("bu")])], language
    )

    assert lone_determinative.value == value
    assert lone_determinative.lemmatizable is False
    assert lone_determinative.language == language
    assert lone_determinative.normalized is False
    assert lone_determinative.unique_lemma == ()

    serialized = {
        "type": "LoneDeterminative",
        "uniqueLemma": [],
        "normalized": False,
        "language": lone_determinative.language.name,
        "lemmatizable": lone_determinative.lemmatizable,
        "alignable": lone_determinative.lemmatizable,
        "erasure": ErasureState.NONE.name,
        "parts": OneOfTokenSchema().dump(parts, many=True),
        "hasVariantAlignment": lone_determinative.has_variant_alignment,
        "hasOmittedAlignment": lone_determinative.has_omitted_alignment,
    }
    assert_token_serialization(lone_determinative, serialized)

    assert lone_determinative == equal
    assert hash(lone_determinative) == hash(equal)

    for not_equal in [other_language, other_parts]:
        assert lone_determinative != not_equal
        assert hash(lone_determinative) != hash(not_equal)

    assert lone_determinative != ValueToken.of(value)


def test_set_language():
    parts = [Determinative.of([Reading.of_name("bu")])]
    language = Language.SUMERIAN
    lone_determinative = LoneDeterminative.of(parts, Language.AKKADIAN)
    expected = LoneDeterminative.of(parts, language)

    assert lone_determinative.set_language(language) == expected
