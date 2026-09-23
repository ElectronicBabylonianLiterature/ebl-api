from ebl.transliteration.domain.signs_transformer import name_arguments
import pytest

import ebl.transliteration.domain.atf as atf
from ebl.tests.asserts import assert_token_serialization
from ebl.transliteration.application.token_schemas import OneOfTokenSchema
from ebl.transliteration.domain.egyptian_metrical_feet_separator_token import (
    EgyptianMetricalFeetSeparator,
)
from ebl.transliteration.domain.enclosure_tokens import BrokenAway
from ebl.transliteration.domain.enclosure_tokens import DocumentOrientedGloss
from ebl.transliteration.domain.enclosure_type import EnclosureType
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
    reading = Reading.of_arguments(
        name_arguments([ValueToken.of("sa"), BrokenAway.open(), ValueToken.of("l")])
    )
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
