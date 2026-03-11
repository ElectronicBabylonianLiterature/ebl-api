import pytest

from ebl.tests.asserts import assert_token_serialization
from ebl.transliteration.application.token_schemas import OneOfTokenSchema
from ebl.transliteration.domain import atf as atf
from ebl.transliteration.domain.enclosure_tokens import BrokenAway
from ebl.transliteration.domain.sign import SignName
from ebl.transliteration.domain.sign_tokens import (
    CompoundGrapheme,
    Divider,
    Grapheme,
    Logogram,
    Number,
    Reading,
)
from ebl.transliteration.domain.tokens import Joiner, ValueToken
from ebl.transliteration.domain.unknown_sign_tokens import UnclearSign, UnidentifiedSign


def test_divider() -> None:
    value = ":"
    modifiers = ("@v",)
    flags = (atf.Flag.UNCERTAIN,)
    divider = Divider.of(value, modifiers, flags)

    expected_value = ":@v?"
    assert divider.value == expected_value
    assert divider.clean_value == ":@v"
    assert divider.get_key() == f"Divider⁝{expected_value}"
    assert divider.lemmatizable is False

    serialized = {
        "type": "Divider",
        "divider": value,
        "modifiers": list(modifiers),
        "flags": ["?"],
    }
    assert_token_serialization(divider, serialized)


def test_unidentified_sign() -> None:
    sign = UnidentifiedSign.of()

    expected_value = "X"
    assert sign.value == expected_value
    assert sign.clean_value == expected_value
    assert sign.get_key() == f"UnidentifiedSign⁝{expected_value}"
    assert sign.flags == ()
    assert sign.lemmatizable is False

    serialized = {"type": "UnidentifiedSign", "flags": []}
    assert_token_serialization(sign, serialized)


def test_unidentified_sign_with_flags() -> None:
    flags = [atf.Flag.DAMAGE]
    sign = UnidentifiedSign.of(flags)

    expected_value = "X#"
    assert sign.value == expected_value
    assert sign.clean_value == "X"
    assert sign.get_key() == f"UnidentifiedSign⁝{expected_value}"
    assert sign.flags == tuple(flags)
    assert sign.lemmatizable is False

    serialized = {"type": "UnidentifiedSign", "flags": ["#"]}
    assert_token_serialization(sign, serialized)


def test_unclear_sign() -> None:
    sign = UnclearSign.of()

    expected_value = "x"
    assert sign.value == expected_value
    assert sign.clean_value == expected_value
    assert sign.get_key() == f"UnclearSign⁝{expected_value}"
    assert sign.flags == ()
    assert sign.lemmatizable is False

    serialized = {"type": "UnclearSign", "flags": []}
    assert_token_serialization(sign, serialized)


def test_unclear_sign_with_flags() -> None:
    flags = [atf.Flag.CORRECTION]
    sign = UnclearSign.of(flags)

    expected_value = "x!"
    assert sign.value == expected_value
    assert sign.clean_value == "x"
    assert sign.get_key() == f"UnclearSign⁝{expected_value}"
    assert sign.flags == tuple(flags)
    assert sign.lemmatizable is False

    serialized = {"type": "UnclearSign", "flags": ["!"]}
    assert_token_serialization(sign, serialized)


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
    assert reading.name_parts == name_parts
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
    assert logogram.name_parts == name_parts
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
    assert number.name_parts == name_parts
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


def test_compound_grapheme() -> None:
    compound = CompoundGrapheme.of(["BI", "IS"])

    expected_value = "|BI.IS|"
    assert compound.name == SignName(expected_value)
    assert compound.value == expected_value
    assert compound.clean_value == expected_value
    assert (
        compound.get_key()
        == f"CompoundGrapheme⁝{expected_value}⟨ValueToken⁝BI⁚ValueToken⁝IS⟩"
    )

    serialized = {"type": "CompoundGrapheme", "compound_parts": ["BI", "IS"]}
    assert_token_serialization(compound, serialized)


@pytest.mark.parametrize(
    "name,modifiers,flags,expected_value,expected_clean_value",
    [
        ("KUR12₁", [], [], "KUR12₁", "KUR12₁"),
        ("KURₓ", [], [], "KURₓ", "KURₓ"),
        ("KU]R", [], [], "KU]R", "KU]R"),
        ("K[UR", [], [], "K[UR", "K[UR"),
        ("KUR", ["@v", "@180"], [], "KUR@v@180", "KUR@v@180"),
        ("KUR", [], [atf.Flag.DAMAGE, atf.Flag.CORRECTION], "KUR#!", "KUR"),
        ("KUR", ["@v"], [atf.Flag.CORRECTION], "KUR@v!", "KUR@v"),
    ],
)
def test_grapheme(name, modifiers, flags, expected_value, expected_clean_value) -> None:
    grapheme = Grapheme.of(name, modifiers, flags)

    assert grapheme.name == name
    assert grapheme.value == expected_value
    assert grapheme.clean_value == expected_clean_value
    assert grapheme.get_key() == f"Grapheme⁝{expected_value}"
    assert grapheme.modifiers == tuple(modifiers)
    assert grapheme.flags == tuple(flags)
    assert grapheme.lemmatizable is False

    serialized = {
        "type": "Grapheme",
        "name": name,
        "modifiers": modifiers,
        "flags": [flag.value for flag in flags],
    }
    assert_token_serialization(grapheme, serialized)
