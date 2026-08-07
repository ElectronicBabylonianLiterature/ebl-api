import pytest

from ebl.tests.asserts import assert_token_serialization
from ebl.transliteration.application.token_schemas import OneOfTokenSchema
from ebl.transliteration.domain import atf as atf
from ebl.transliteration.domain.enclosure_tokens import BrokenAway
from ebl.transliteration.domain.sign import SignName
from ebl.transliteration.domain.sign_tokens import (
    Grapheme,
    Logogram,
    Reading,
)
from ebl.transliteration.domain.tokens import Joiner, ValueToken


@pytest.mark.parametrize(
    "name_parts,sub_index,modifiers,flags,sign,surrogate,expected_value,"
    "expected_clean_value,expected_name",
    [
        ((ValueToken.of("KUR"),), 1, [], [], None, [], "KUR", "KUR", "KUR"),
        ((ValueToken.of("KURʾ"),), 1, [], [], None, [], "KURʾ", "KURʾ", "KURʾ"),
        ((ValueToken.of("ʾ"),), 1, [], [], None, [], "ʾ", "ʾ", "ʾ"),
        (
            (ValueToken.of("KU"), BrokenAway.open(), ValueToken.of("R")),
            1,
            [],
            [],
            None,
            [],
            "KU[R",
            "KUR",
            "KUR",
        ),
        (
            (ValueToken.of("K"), BrokenAway.close(), ValueToken.of("UR")),
            1,
            [],
            [],
            None,
            [],
            "K]UR",
            "KUR",
            "KUR",
        ),
        ((ValueToken.of("KUR"),), None, [], [], None, [], "KURₓ", "KURₓ", "KUR"),
        ((ValueToken.of("KUR"),), 0, [], [], None, [], "KUR₀", "KUR₀", "KUR"),
        (
            (ValueToken.of("KUR"),),
            1,
            [],
            [],
            Grapheme.of(SignName("KUR")),
            [],
            "KUR(KUR)",
            "KUR(KUR)",
            "KUR",
        ),
        (
            (ValueToken.of("KUR"),),
            1,
            [],
            [],
            None,
            [Reading.of_name("kur"), Joiner.hyphen(), Reading.of_name("kur")],
            "KUR<(kur-kur)>",
            "KUR<(kur-kur)>",
            "KUR",
        ),
        (
            (ValueToken.of("KUR"),),
            1,
            ["@v", "@180"],
            [],
            None,
            [],
            "KUR@v@180",
            "KUR@v@180",
            "KUR",
        ),
        (
            (ValueToken.of("KUR"),),
            1,
            [],
            [atf.Flag.DAMAGE, atf.Flag.CORRECTION],
            None,
            [],
            "KUR#!",
            "KUR",
            "KUR",
        ),
        (
            (ValueToken.of("KUR"),),
            10,
            ["@v"],
            [atf.Flag.CORRECTION],
            Grapheme.of(SignName("KUR")),
            [],
            "KUR₁₀@v!(KUR)",
            "KUR₁₀@v(KUR)",
            "KUR",
        ),
    ],
)
def test_logogram(
    name_parts,
    sub_index,
    modifiers,
    flags,
    sign,
    surrogate,
    expected_value,
    expected_clean_value,
    expected_name,
) -> None:
    logogram = Logogram.of(name_parts, sub_index, modifiers, flags, sign, surrogate)

    expected_parts = (*name_parts, sign) if sign else name_parts
    assert logogram.value == expected_value
    assert logogram.clean_value == expected_clean_value
    assert (
        logogram.get_key()
        == f"Logogram⁝{expected_value}⟨{'⁚'.join(token.get_key() for token in expected_parts)}⟩"
    )
    assert logogram.name_tokens == tuple(name_parts)
    assert logogram.name == expected_name
    assert logogram.modifiers == tuple(modifiers)
    assert logogram.flags == tuple(flags)
    assert logogram.lemmatizable is False
    assert logogram.sign == sign
    assert logogram.surrogate == tuple(surrogate)

    serialized = {
        "type": "Logogram",
        "name": expected_name,
        "nameParts": OneOfTokenSchema().dump(name_parts, many=True),
        "subIndex": sub_index,
        "modifiers": modifiers,
        "flags": [flag.value for flag in flags],
        "surrogate": OneOfTokenSchema().dump(surrogate, many=True),
        "sign": sign and OneOfTokenSchema().dump(sign),
    }
    assert_token_serialization(logogram, serialized)
