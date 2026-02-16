import pytest

import ebl.transliteration.domain.atf as atf
from ebl.lemmatization.domain.lemmatization import (
    LemmatizationError,
    LemmatizationToken,
)
from ebl.tests.asserts import assert_token_serialization
from ebl.transliteration.application.token_schemas import OneOfTokenSchema
from ebl.transliteration.domain.alignment import AlignmentError, AlignmentToken
from ebl.transliteration.domain.egyptian_metrical_feet_separator_token import (
    EgyptianMetricalFeetSeparator,
)
from ebl.transliteration.domain.enclosure_tokens import BrokenAway
from ebl.transliteration.domain.enclosure_tokens import DocumentOrientedGloss
from ebl.transliteration.domain.enclosure_type import EnclosureType
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.sign_tokens import Divider, Reading
from ebl.transliteration.domain.tokens import (
    Column,
    CommentaryProtocol,
    ErasureState,
    Joiner,
    LanguageShift,
    Tabulation,
    UnknownNumberOfSigns,
    ValueToken,
    Variant,
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


def test_unknown_number_of_signs():
    unknown_number_of_signs = UnknownNumberOfSigns(
        frozenset({EnclosureType.BROKEN_AWAY}), ErasureState.NONE
    )

    expected_value = "..."
    assert unknown_number_of_signs.value == expected_value
    assert unknown_number_of_signs.clean_value == expected_value
    assert unknown_number_of_signs.get_key() == f"UnknownNumberOfSigns⁝{expected_value}"
    assert unknown_number_of_signs.lemmatizable is False

    serialized = {"type": "UnknownNumberOfSigns"}
    assert_token_serialization(unknown_number_of_signs, serialized)


def test_egyptian_metrical_feet_separator():
    egyptian_metrical_feet_separator = EgyptianMetricalFeetSeparator.of(
        (atf.Flag.UNCERTAIN,)
    )
    expected_value = "•?"
    assert egyptian_metrical_feet_separator.value == expected_value
    assert egyptian_metrical_feet_separator.clean_value == "•"
    assert (
        egyptian_metrical_feet_separator.get_key()
        == f"EgyptianMetricalFeetSeparator⁝{expected_value}"
    )
    assert egyptian_metrical_feet_separator.lemmatizable is False

    serialized = {"type": "EgyptianMetricalFeetSeparator", "flags": ["?"]}
    assert_token_serialization(egyptian_metrical_feet_separator, serialized)


def test_tabulation():
    value = "($___$)"
    tabulation = Tabulation.of()

    assert tabulation.value == value
    assert tabulation.clean_value == value
    assert tabulation.get_key() == f"Tabulation⁝{value}"
    assert tabulation.lemmatizable is False

    serialized = {"type": "Tabulation"}
    assert_token_serialization(tabulation, serialized)


@pytest.mark.parametrize("protocol_enum", atf.CommentaryProtocol)
def test_commentary_protocol(protocol_enum):
    value = protocol_enum.value
    protocol = CommentaryProtocol.of(value)

    assert protocol.value == value
    assert protocol.clean_value == value
    assert protocol.get_key() == f"CommentaryProtocol⁝{value}"
    assert protocol.lemmatizable is False
    assert protocol.protocol == protocol_enum

    serialized = {"type": "CommentaryProtocol"}
    assert_token_serialization(protocol, serialized)


def test_column():
    column = Column.of()

    expected_value = "&"
    assert column.value == expected_value
    assert column.clean_value == expected_value
    assert column.get_key() == f"Column⁝{expected_value}"
    assert column.lemmatizable is False

    serialized = {"type": "Column", "number": None}
    assert_token_serialization(column, serialized)


def test_column_with_number():
    column = Column.of(1)

    expected_value = "&1"
    assert column.value == expected_value
    assert column.clean_value == expected_value
    assert column.get_key() == f"Column⁝{expected_value}"
    assert column.lemmatizable is False

    serialized = {"type": "Column", "number": 1}
    assert_token_serialization(column, serialized)


def test_invalid_column():
    with pytest.raises(ValueError):
        Column.of(-1)


def test_variant():
    reading = Reading.of([ValueToken.of("sa"), BrokenAway.open(), ValueToken.of("l")])
    divider = Divider.of(":")
    variant = Variant.of(reading, divider)

    expected_value = "sa[l/:"
    assert variant.value == expected_value
    assert variant.clean_value == "sal/:"
    assert variant.tokens == (reading, divider)
    assert variant.parts == variant.tokens
    assert (
        variant.get_key()
        == f"Variant⁝{expected_value}⟨{'⁚'.join(token.get_key() for token in variant.tokens)}⟩"
    )
    assert variant.lemmatizable is False

    serialized = {
        "type": "Variant",
        "tokens": OneOfTokenSchema().dump([reading, divider], many=True),
    }
    assert_token_serialization(variant, serialized)


@pytest.mark.parametrize(
    "joiner,expected_value",
    [
        (Joiner.dot(), "."),
        (Joiner.hyphen(), "-"),
        (Joiner.colon(), ":"),
        (Joiner.plus(), "+"),
    ],
)
def test_joiner(joiner, expected_value):
    assert joiner.value == expected_value
    assert joiner.clean_value == expected_value
    assert joiner.get_key() == f"Joiner⁝{expected_value}"
    assert joiner.lemmatizable is False

    serialized = {"type": "Joiner"}
    assert_token_serialization(joiner, serialized)
