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
from ebl.transliteration.domain.tokens import ValueToken


@pytest.mark.parametrize(
    "name_parts,modifiers,flags,sign,expected_value,expected_clean_value,expected_name",
    [
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
    ],
)
def test_number(
    name_parts,
    modifiers,
    flags,
    sign,
    expected_value,
    expected_clean_value,
    expected_name,
) -> None:
    number = Number.of(name_parts, modifiers, flags, sign)

    expected_sub_index = 1
    expected_parts = (*name_parts, sign) if sign else name_parts
    assert number.value == expected_value
    assert number.clean_value == expected_clean_value
    assert (
        number.get_key()
        == f"Number⁝{expected_value}⟨{'⁚'.join(token.get_key() for token in expected_parts)}⟩"
    )
    assert number.name_tokens == tuple(name_parts)
    assert number.name == expected_name
    assert number.sub_index == expected_sub_index
    assert number.modifiers == tuple(modifiers)
    assert number.flags == tuple(flags)
    assert number.lemmatizable is False
    assert number.sign == sign

    serialized = {
        "type": "Number",
        "name": expected_name,
        "nameParts": OneOfTokenSchema().dump(name_parts, many=True),
        "modifiers": modifiers,
        "subIndex": expected_sub_index,
        "flags": [flag.value for flag in flags],
        "sign": sign and OneOfTokenSchema().dump(sign),
    }
    assert_token_serialization(number, serialized)
