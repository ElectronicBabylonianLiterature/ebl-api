import pytest

from ebl.tests.asserts import assert_token_serialization
from ebl.transliteration.application.token_schemas import (
    dump_token,
    dump_tokens,
    load_token,
)
from ebl.transliteration.domain import atf as atf
from ebl.transliteration.domain.enclosure_tokens import BrokenAway
from ebl.transliteration.domain.sign_tokens import (
    CompoundGrapheme,
    Divider,
    Grapheme,
    Logogram,
    Number,
    Reading,
    UnclearSign,
    UnidentifiedSign,
)
from ebl.transliteration.domain.tokens import Joiner, ValueToken


def test_divider():
    value = ":"
    modifiers = ("@v",)
    flags = (atf.Flag.UNCERTAIN,)
    divider = Divider.of(value, modifiers, flags)

    expected_value = ":@v?"
    assert divider.value == expected_value
    assert divider.get_key() == f"Divider⁝{expected_value}"
    assert divider.lemmatizable is False

    serialized = {
        "type": "Divider",
        "value": expected_value,
        "divider": value,
        "modifiers": list(modifiers),
        "flags": ["?"],
    }
    assert_token_serialization(divider, serialized)


def test_unidentified_sign():
    sign = UnidentifiedSign()

    expected_value = "X"
    assert sign.value == expected_value
    assert sign.get_key() == f"UnidentifiedSign⁝{expected_value}"
    assert sign.flags == tuple()
    assert sign.lemmatizable is False

    serialized = {
        "type": "UnidentifiedSign",
        "value": expected_value,
        "flags": [],
    }
    assert_token_serialization(sign, serialized)


def test_unidentified_sign_with_flags():
    flags = [atf.Flag.DAMAGE]
    sign = UnidentifiedSign(flags)

    expected_value = "X#"
    assert sign.value == expected_value
    assert sign.get_key() == f"UnidentifiedSign⁝{expected_value}"
    assert sign.flags == tuple(flags)
    assert sign.lemmatizable is False

    serialized = {
        "type": "UnidentifiedSign",
        "value": expected_value,
        "flags": ["#"],
    }
    assert_token_serialization(sign, serialized)


def test_unclear_sign():
    sign = UnclearSign()

    expected_value = "x"
    assert sign.value == expected_value
    assert sign.get_key() == f"UnclearSign⁝{expected_value}"
    assert sign.flags == tuple()
    assert sign.lemmatizable is False

    serialized = {
        "type": "UnclearSign",
        "value": expected_value,
        "flags": [],
    }
    assert_token_serialization(sign, serialized)


def test_unclear_sign_with_flags():
    flags = [atf.Flag.CORRECTION]
    sign = UnclearSign(flags)

    expected_value = "x!"
    assert sign.value == expected_value
    assert sign.get_key() == f"UnclearSign⁝{expected_value}"
    assert sign.flags == tuple(flags)
    assert sign.lemmatizable is False

    serialized = {
        "type": "UnclearSign",
        "value": expected_value,
        "flags": ["!"],
    }
    assert_token_serialization(sign, serialized)


@pytest.mark.parametrize(
    "name_parts,sub_index,modifiers,flags,sign,expected_value,expected_name",
    [
        ((ValueToken("kur"),), 1, [], [], None, "kur", "kur"),
        ((ValueToken("kurʾ"),), 1, [], [], None, "kurʾ", "kurʾ"),
        ((ValueToken("ʾ"),), 1, [], [], None, "ʾ", "ʾ"),
        (
            (ValueToken("k"), BrokenAway.open(), ValueToken("ur")),
            1,
            [],
            [],
            None,
            "k[ur",
            "kur",
        ),
        (
            (ValueToken("ku"), BrokenAway.close(), ValueToken("r")),
            1,
            [],
            [],
            None,
            "ku]r",
            "kur",
        ),
        ((ValueToken("kur"),), None, [], [], None, "kurₓ", "kur"),
        ((ValueToken("kur"),), 0, [], [], None, "kur₀", "kur"),
        ((ValueToken("kur"),), 1, [], [], Grapheme.of("KUR"), "kur(KUR)", "kur"),
        ((ValueToken("kur"),), 1, ["@v", "@180"], [], None, "kur@v@180", "kur"),
        (
            (ValueToken("kur"),),
            1,
            [],
            [atf.Flag.DAMAGE, atf.Flag.CORRECTION],
            None,
            "kur#!",
            "kur",
        ),
        (
            (ValueToken("kur"),),
            10,
            ["@v"],
            [atf.Flag.CORRECTION],
            Grapheme.of("KUR"),
            "kur₁₀@v!(KUR)",
            "kur",
        ),
    ],
)
def test_reading(
    name_parts, sub_index, modifiers, flags, sign, expected_value, expected_name
):
    reading = Reading.of(name_parts, sub_index, modifiers, flags, sign)

    expected_parts = (*name_parts, sign) if sign else name_parts
    assert reading.value == expected_value
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
        "value": expected_value,
        "name": expected_name,
        "nameParts": [dump_token(token) for token in name_parts],
        "subIndex": sub_index,
        "modifiers": modifiers,
        "flags": [flag.value for flag in flags],
        "sign": sign and dump_token(sign),
    }
    assert_token_serialization(reading, serialized)


def test_load_old_style_reading():
    name = "kur"
    sub_index = 1
    flags = []
    modifiers = []
    sign = "KUR"
    reading = Reading.of_name(name, sub_index, modifiers, flags, ValueToken(sign))

    serialized = {
        "type": "Reading",
        "value": "kur(KUR)",
        "name": name,
        "subIndex": sub_index,
        "modifiers": modifiers,
        "flags": flags,
        "sign": sign,
    }
    assert load_token(serialized) == reading


@pytest.mark.parametrize("name,sub_index", [("kur", -1), ("KUR", 1)])
@pytest.mark.skip
def test_invalid_reading(name, sub_index):
    with pytest.raises(ValueError):
        Reading.of(name, sub_index)


@pytest.mark.parametrize(
    "name_parts,sub_index,modifiers,flags,sign,surrogate,expected_value,expected_name",
    [
        ((ValueToken("KUR"),), 1, [], [], None, [], "KUR", "KUR"),
        ((ValueToken("KURʾ"),), 1, [], [], None, [], "KURʾ", "KURʾ"),
        ((ValueToken("ʾ"),), 1, [], [], None, [], "ʾ", "ʾ"),
        (
            (ValueToken("KU"), BrokenAway.open(), ValueToken("R")),
            1,
            [],
            [],
            None,
            [],
            "KU[R",
            "KUR",
        ),
        (
            (ValueToken("K"), BrokenAway.close(), ValueToken("UR")),
            1,
            [],
            [],
            None,
            [],
            "K]UR",
            "KUR",
        ),
        ((ValueToken("KUR"),), None, [], [], None, [], "KURₓ", "KUR"),
        ((ValueToken("KUR"),), 0, [], [], None, [], "KUR₀", "KUR"),
        ((ValueToken("KUR"),), 1, [], [], Grapheme.of("KUR"), [], "KUR(KUR)", "KUR"),
        (
            (ValueToken("KUR"),),
            1,
            [],
            [],
            None,
            [Reading.of_name("kur"), Joiner(atf.Joiner.HYPHEN), Reading.of_name("kur")],
            "KUR<(kur-kur)>",
            "KUR",
        ),
        ((ValueToken("KUR"),), 1, ["@v", "@180"], [], None, [], "KUR@v@180", "KUR"),
        (
            (ValueToken("KUR"),),
            1,
            [],
            [atf.Flag.DAMAGE, atf.Flag.CORRECTION],
            None,
            [],
            "KUR#!",
            "KUR",
        ),
        (
            (ValueToken("KUR"),),
            10,
            ["@v"],
            [atf.Flag.CORRECTION],
            Grapheme.of("KUR"),
            [],
            "KUR₁₀@v!(KUR)",
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
    expected_name,
):
    logogram = Logogram.of(name_parts, sub_index, modifiers, flags, sign, surrogate)

    expected_parts = (*name_parts, sign) if sign else name_parts
    assert logogram.value == expected_value
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
        "value": expected_value,
        "name": expected_name,
        "nameParts": [dump_token(token) for token in name_parts],
        "subIndex": sub_index,
        "modifiers": modifiers,
        "flags": [flag.value for flag in flags],
        "surrogate": dump_tokens(surrogate),
        "sign": sign and dump_token(sign),
    }
    assert_token_serialization(logogram, serialized)


@pytest.mark.parametrize("name,sub_index", [("KUR", -1), ("kur", 1)])
@pytest.mark.skip
def test_invalid_logogram(name, sub_index):
    with pytest.raises(ValueError):
        Logogram.of(name, sub_index)


@pytest.mark.parametrize(
    "name_parts,modifiers,flags,sign,expected_value, expected_name",
    [
        ((ValueToken("1"),), [], [], None, "1", "1"),
        (
            (ValueToken("1"), BrokenAway.open(), ValueToken("4")),
            [],
            [],
            None,
            "1[4",
            "14",
        ),
        (
            (ValueToken("1"), BrokenAway.close(), ValueToken("0")),
            [],
            [],
            None,
            "1]0",
            "10",
        ),
        ((ValueToken("1"),), [], [], Grapheme.of("KUR"), "1(KUR)", "1"),
        ((ValueToken("1"),), ["@v", "@180"], [], None, "1@v@180", "1"),
        (
            (ValueToken("1"),),
            [],
            [atf.Flag.DAMAGE, atf.Flag.CORRECTION],
            None,
            "1#!",
            "1",
        ),
        (
            (ValueToken("1"),),
            ["@v"],
            [atf.Flag.CORRECTION],
            Grapheme.of("KUR"),
            "1@v!(KUR)",
            "1",
        ),
    ],
)
def test_number(name_parts, modifiers, flags, sign, expected_value, expected_name):
    number = Number.of(name_parts, modifiers, flags, sign)

    expected_sub_index = 1
    expected_parts = (*name_parts, sign) if sign else name_parts
    assert number.value == expected_value
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
        "value": expected_value,
        "name": expected_name,
        "nameParts": [dump_token(token) for token in name_parts],
        "modifiers": modifiers,
        "subIndex": expected_sub_index,
        "flags": [flag.value for flag in flags],
        "sign": sign and dump_token(sign),
    }
    assert_token_serialization(number, serialized)


@pytest.mark.parametrize("name", ["-1", "kur", "KUR"])
@pytest.mark.skip
def test_invalid_number(name):
    with pytest.raises(ValueError):
        Number.of(name)


def test_compound_grapheme():
    value = "|BI.IS|"
    compound = CompoundGrapheme(value)

    assert compound.value == value
    assert compound.get_key() == f"CompoundGrapheme⁝{value}"

    serialized = {
        "type": "CompoundGrapheme",
        "value": value,
    }
    assert_token_serialization(compound, serialized)


@pytest.mark.parametrize(
    "name,modifiers,flags,expected_value",
    [
        ("KUR12₁", [], [], "KUR12₁"),
        ("KURₓ", [], [], "KURₓ"),
        ("KU]R", [], [], "KU]R"),
        ("K[UR", [], [], "K[UR"),
        ("KUR", ["@v", "@180"], [], "KUR@v@180"),
        ("KUR", [], [atf.Flag.DAMAGE, atf.Flag.CORRECTION], "KUR#!"),
        ("KUR", ["@v"], [atf.Flag.CORRECTION], "KUR@v!"),
    ],
)
def test_grapheme(name, modifiers, flags, expected_value):
    grapheme = Grapheme.of(name, modifiers, flags)

    assert grapheme.name == name
    assert grapheme.value == expected_value
    assert grapheme.get_key() == f"Grapheme⁝{expected_value}"
    assert grapheme.modifiers == tuple(modifiers)
    assert grapheme.flags == tuple(flags)
    assert grapheme.lemmatizable is False

    serialized = {
        "type": "Grapheme",
        "value": expected_value,
        "name": name,
        "modifiers": modifiers,
        "flags": [flag.value for flag in flags],
    }
    assert_token_serialization(grapheme, serialized)
