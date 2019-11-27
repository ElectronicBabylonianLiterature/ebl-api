import pytest

from ebl.transliteration.domain import atf as atf
from ebl.transliteration.domain.sign_tokens import (
    Divider,
    Logogram,
    Number,
    Reading,
    UnclearSign,
    UnidentifiedSign,
)


def test_divider():
    value = ":"
    modifiers = ("@v",)
    flags = (atf.Flag.UNCERTAIN,)
    divider = Divider(value, modifiers, flags)

    expected_value = ":@v?"
    assert divider.value == expected_value
    assert divider.get_key() == f"Divider⁝{expected_value}"
    assert divider.lemmatizable is False
    assert divider.to_dict() == {
        "type": "Divider",
        "value": expected_value,
        "divider": value,
        "modifiers": list(modifiers),
        "flags": ["?"],
    }


def test_unidentified_sign():
    sign = UnidentifiedSign()

    expected_value = "X"
    assert sign.value == expected_value
    assert sign.get_key() == f"UnidentifiedSign⁝{expected_value}"
    assert sign.flags == tuple()
    assert sign.lemmatizable is False
    assert sign.to_dict() == {
        "type": "UnidentifiedSign",
        "value": expected_value,
        "flags": [],
    }


def test_unidentified_sign_with_flags():
    flags = [atf.Flag.DAMAGE]
    sign = UnidentifiedSign(flags)

    expected_value = "X#"
    assert sign.value == expected_value
    assert sign.get_key() == f"UnidentifiedSign⁝{expected_value}"
    assert sign.flags == tuple(flags)
    assert sign.lemmatizable is False
    assert sign.to_dict() == {
        "type": "UnidentifiedSign",
        "value": expected_value,
        "flags": ["#"],
    }


def test_unclear_sign():
    sign = UnclearSign()

    expected_value = "x"
    assert sign.value == expected_value
    assert sign.get_key() == f"UnclearSign⁝{expected_value}"
    assert sign.flags == tuple()
    assert sign.lemmatizable is False
    assert sign.to_dict() == {
        "type": "UnclearSign",
        "value": expected_value,
        "flags": [],
    }


def test_unclear_sign_with_flags():
    flags = [atf.Flag.CORRECTION]
    sign = UnclearSign(flags)

    expected_value = "x!"
    assert sign.value == expected_value
    assert sign.get_key() == f"UnclearSign⁝{expected_value}"
    assert sign.flags == tuple(flags)
    assert sign.lemmatizable is False
    assert sign.to_dict() == {
        "type": "UnclearSign",
        "value": expected_value,
        "flags": ["!"],
    }


@pytest.mark.parametrize(
    "name,sub_index,modifiers,flags,sign,expected_value",
    [
        ("kur", 1, [], [], None, "kur"),
        ("kur", 0, [], [], None, "kur₀"),
        ("kur", 1, [], [], "KUR", "kur(KUR)"),
        ("kur", 1, ["@v", "@180"], [], None, "kur@v@180"),
        ("kur", 1, [], [atf.Flag.DAMAGE, atf.Flag.CORRECTION], None, "kur#!"),
        ("kur", 10, ["@v"], [atf.Flag.CORRECTION], "KUR", "kur₁₀@v!(KUR)"),
    ],
)
def test_reading(name, sub_index, modifiers, flags, sign, expected_value):
    reading = Reading.of(name, sub_index, modifiers, flags, sign)

    assert reading.value == expected_value
    assert reading.get_key() == f"Reading⁝{expected_value}"
    assert reading.modifiers == tuple(modifiers)
    assert reading.flags == tuple(flags)
    assert reading.lemmatizable is False
    assert reading.sign == sign
    assert reading.to_dict() == {
        "type": "Reading",
        "value": expected_value,
        "name": name,
        "subIndex": sub_index,
        "modifiers": modifiers,
        "flags": [flag.value for flag in flags],
        "sign": sign,
    }


@pytest.mark.parametrize("name,sub_index", [("kur", -1), ("KUR", 1)])
def test_invalid_reading(name, sub_index):
    with pytest.raises(ValueError):
        Reading.of(name, sub_index)


@pytest.mark.parametrize(
    "name,sub_index,modifiers,flags,sign,expected_value",
    [
        ("KUR", 1, [], [], None, "KUR"),
        ("KUR", 0, [], [], None, "KUR₀"),
        ("KUR", 1, [], [], "KUR", "KUR(KUR)"),
        ("KUR", 1, ["@v", "@180"], [], None, "KUR@v@180"),
        ("KUR", 1, [], [atf.Flag.DAMAGE, atf.Flag.CORRECTION], None, "KUR#!"),
        ("KUR", 10, ["@v"], [atf.Flag.CORRECTION], "KUR", "KUR₁₀@v!(KUR)"),
    ],
)
def test_logogram(name, sub_index, modifiers, flags, sign, expected_value):
    logogram = Logogram.of(name, sub_index, modifiers, flags, sign)

    assert logogram.value == expected_value
    assert logogram.get_key() == f"Logogram⁝{expected_value}"
    assert logogram.modifiers == tuple(modifiers)
    assert logogram.flags == tuple(flags)
    assert logogram.lemmatizable is False
    assert logogram.sign == sign
    assert logogram.to_dict() == {
        "type": "Logogram",
        "value": expected_value,
        "name": name,
        "subIndex": sub_index,
        "modifiers": modifiers,
        "flags": [flag.value for flag in flags],
        "sign": sign,
    }


@pytest.mark.parametrize("name,sub_index", [("KUR", -1), ("kur", 1)])
def test_invalid_logogram(name, sub_index):
    with pytest.raises(ValueError):
        Logogram.of(name, sub_index)


@pytest.mark.parametrize(
    "numeral,modifiers,flags,sign,expected_value",
    [
        (1, [], [], None, "1"),
        (14, [], [], None, "14"),
        (1, [], [], "KUR", "1(KUR)"),
        (1, ["@v", "@180"], [], None, "1@v@180"),
        (1, [], [atf.Flag.DAMAGE, atf.Flag.CORRECTION], None, "1#!"),
        (1, ["@v"], [atf.Flag.CORRECTION], "KUR", "1@v!(KUR)"),
    ],
)
def test_number(numeral, modifiers, flags, sign, expected_value):
    number = Number.of(numeral, modifiers, flags, sign)

    expected_sub_index = 1
    assert number.value == expected_value
    assert number.get_key() == f"Number⁝{expected_value}"
    assert number.sub_index == expected_sub_index
    assert number.modifiers == tuple(modifiers)
    assert number.flags == tuple(flags)
    assert number.lemmatizable is False
    assert number.sign == sign
    assert number.to_dict() == {
        "type": "Number",
        "value": expected_value,
        "numeral": numeral,
        "modifiers": modifiers,
        "subIndex": expected_sub_index,
        "flags": [flag.value for flag in flags],
        "sign": sign,
    }


@pytest.mark.parametrize("numeral", [0, -1])
def test_invalid_number(numeral):
    with pytest.raises(ValueError):
        Number.of(numeral)
