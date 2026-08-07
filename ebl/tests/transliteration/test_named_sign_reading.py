import pytest

from ebl.tests.asserts import assert_token_serialization
from ebl.transliteration.application.token_schemas import OneOfTokenSchema
from ebl.transliteration.domain import atf as atf
from ebl.transliteration.domain.enclosure_tokens import BrokenAway
from ebl.transliteration.domain.sign import SignName
from ebl.transliteration.domain.sign_tokens import (
    Grapheme,
    Reading,
)
from ebl.transliteration.domain.tokens import ValueToken


@pytest.mark.parametrize(
    "name_parts,sub_index,modifiers,flags,sign,expected_value,expected_clean_value,"
    "expected_name",
    [
        ((ValueToken.of("kur"),), 1, [], [], None, "kur", "kur", "kur"),
        ((ValueToken.of("kurʾ"),), 1, [], [], None, "kurʾ", "kurʾ", "kurʾ"),
        ((ValueToken.of("ʾ"),), 1, [], [], None, "ʾ", "ʾ", "ʾ"),
        (
            (ValueToken.of("k"), BrokenAway.open(), ValueToken.of("ur")),
            1,
            [],
            [],
            None,
            "k[ur",
            "kur",
            "kur",
        ),
        (
            (ValueToken.of("ku"), BrokenAway.close(), ValueToken.of("r")),
            1,
            [],
            [],
            None,
            "ku]r",
            "kur",
            "kur",
        ),
        ((ValueToken.of("kur"),), None, [], [], None, "kurₓ", "kurₓ", "kur"),
        ((ValueToken.of("kur"),), 0, [], [], None, "kur₀", "kur₀", "kur"),
        (
            (ValueToken.of("kur"),),
            1,
            [],
            [],
            Grapheme.of(SignName("KUR")),
            "kur(KUR)",
            "kur(KUR)",
            "kur",
        ),
        (
            (ValueToken.of("kur"),),
            1,
            ["@v", "@180"],
            [],
            None,
            "kur@v@180",
            "kur@v@180",
            "kur",
        ),
        (
            (ValueToken.of("kur"),),
            1,
            [],
            [atf.Flag.DAMAGE, atf.Flag.CORRECTION],
            None,
            "kur#!",
            "kur",
            "kur",
        ),
        (
            (ValueToken.of("kur"),),
            10,
            ["@v"],
            [atf.Flag.CORRECTION],
            Grapheme.of(SignName("KUR")),
            "kur₁₀@v!(KUR)",
            "kur₁₀@v(KUR)",
            "kur",
        ),
    ],
)
def test_reading(
    name_parts,
    sub_index,
    modifiers,
    flags,
    sign,
    expected_value,
    expected_clean_value,
    expected_name,
) -> None:
    reading = Reading.of(name_parts, sub_index, modifiers, flags, sign)

    expected_parts = (*name_parts, sign) if sign else name_parts
    assert reading.value == expected_value
    assert reading.clean_value == expected_clean_value
    assert (
        reading.get_key()
        == f"Reading⁝{expected_value}⟨{'⁚'.join(token.get_key() for token in expected_parts)}⟩"
    )
    assert reading.name_tokens == tuple(name_parts)
    assert reading.name == expected_name
    assert reading.modifiers == tuple(modifiers)
    assert reading.flags == tuple(flags)
    assert reading.lemmatizable is False
    assert reading.sign == sign

    serialized = {
        "type": "Reading",
        "name": expected_name,
        "nameParts": OneOfTokenSchema().dump(name_parts, many=True),
        "subIndex": sub_index,
        "modifiers": modifiers,
        "flags": [flag.value for flag in flags],
        "sign": sign and OneOfTokenSchema().dump(sign),
    }
    assert_token_serialization(reading, serialized)
