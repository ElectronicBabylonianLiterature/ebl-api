from typing import NamedTuple, Optional, Sequence, Tuple

import pytest

from ebl.tests.asserts import assert_token_serialization
from ebl.transliteration.application.token_schemas import OneOfTokenSchema
from ebl.transliteration.domain import atf as atf
from ebl.transliteration.domain.enclosure_tokens import BrokenAway
from ebl.transliteration.domain.sign import SignName
from ebl.transliteration.domain.sign_tokens import (
    Grapheme,
    Number,
)
from ebl.transliteration.domain.tokens import Token, ValueToken


class NumberCase(NamedTuple):
    name_parts: Sequence[Token]
    modifiers: Sequence[str]
    flags: Sequence[atf.Flag]
    sign: Optional[Token]
    expected_value: str
    expected_clean_value: str
    expected_name: str


CASES = [
    ((ValueToken.of("1"),), [], [], None, "1", "1", "1"),
    (
        (ValueToken.of("1"), BrokenAway.open(), ValueToken.of("4")),
        [],
        [],
        None,
        "1[4",
        "14",
        "14",
    ),
    (
        (ValueToken.of("1"), BrokenAway.close(), ValueToken.of("0")),
        [],
        [],
        None,
        "1]0",
        "10",
        "10",
    ),
    (
        (ValueToken.of("1"),),
        [],
        [],
        Grapheme.of(SignName("KUR")),
        "1(KUR)",
        "1(KUR)",
        "1",
    ),
    (
        (ValueToken.of("4"),),
        [],
        [atf.Flag.DAMAGE],
        Grapheme.of(SignName("BAN₂")),
        "4#(BAN₂)",
        "4(BAN₂)",
        "4",
    ),
    (
        (ValueToken.of("4"),),
        [],
        [atf.Flag.DAMAGE, atf.Flag.UNCERTAIN],
        Grapheme.of(SignName("BAN₂")),
        "4#?(BAN₂)",
        "4(BAN₂)",
        "4",
    ),
    ((ValueToken.of("1"),), ["@v", "@180"], [], None, "1@v@180", "1@v@180", "1"),
    (
        (ValueToken.of("1"),),
        [],
        [atf.Flag.DAMAGE, atf.Flag.CORRECTION],
        None,
        "1#!",
        "1",
        "1",
    ),
    (
        (ValueToken.of("1"),),
        ["@v"],
        [atf.Flag.CORRECTION],
        Grapheme.of(SignName("KUR")),
        "1@v!(KUR)",
        "1@v(KUR)",
        "1",
    ),
]

EXPECTED_SUB_INDEX = 1


@pytest.mark.parametrize("case", [NumberCase(*case) for case in CASES])
def test_number(case: NumberCase) -> None:
    number = Number.of(case.name_parts, case.modifiers, case.flags, case.sign)

    sign = case.sign
    expected_parts: Tuple[Token, ...] = tuple(case.name_parts) + (
        (sign,) if sign is not None else ()
    )
    assert number.value == case.expected_value
    assert number.clean_value == case.expected_clean_value
    assert (
        number.get_key() == f"Number⁝{case.expected_value}"
        f"⟨{'⁚'.join(token.get_key() for token in expected_parts)}⟩"
    )
    assert number.name_tokens == tuple(case.name_parts)
    assert number.name == case.expected_name
    assert number.sub_index == EXPECTED_SUB_INDEX
    assert number.modifiers == tuple(case.modifiers)
    assert number.flags == tuple(case.flags)
    assert number.lemmatizable is False
    assert number.sign == case.sign

    serialized = {
        "type": "Number",
        "name": case.expected_name,
        "nameParts": OneOfTokenSchema().dump(case.name_parts, many=True),
        "modifiers": case.modifiers,
        "subIndex": EXPECTED_SUB_INDEX,
        "flags": [flag.value for flag in case.flags],
        "sign": case.sign and OneOfTokenSchema().dump(case.sign),
    }
    assert_token_serialization(number, serialized)
