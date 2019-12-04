import pytest

from ebl.transliteration.domain import atf as atf
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
from ebl.transliteration.domain.token_schemas import dump_token, dump_tokens, load_token
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
    assert dump_token(divider) == serialized
    assert load_token(serialized) == divider


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
    assert dump_token(sign) == serialized
    assert load_token(serialized) == sign


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
    assert dump_token(sign) == serialized
    assert load_token(serialized) == sign


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
    assert dump_token(sign) == serialized
    assert load_token(serialized) == sign


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
    assert dump_token(sign) == serialized
    assert load_token(serialized) == sign


@pytest.mark.parametrize(
    "name,sub_index,modifiers,flags,sign,expected_value",
    [
        ("kur", 1, [], [], None, "kur"),
        ("kurʾ", 1, [], [], None, "kurʾ"),
        ("ʾ", 1, [], [], None, "ʾ"),
        ("k[ur", 1, [], [], None, "k[ur"),
        ("ku]r", 1, [], [], None, "ku]r"),
        ("kur", 0, [], [], None, "kur₀"),
        ("kur", 1, [], [], Grapheme.of("KUR"), "kur(KUR)"),
        ("kur", 1, ["@v", "@180"], [], None, "kur@v@180"),
        ("kur", 1, [], [atf.Flag.DAMAGE, atf.Flag.CORRECTION], None, "kur#!"),
        ("kur", 10, ["@v"], [atf.Flag.CORRECTION], Grapheme.of("KUR"), "kur₁₀@v!(KUR)"),
    ],
)
def test_reading(name, sub_index, modifiers, flags, sign, expected_value):
    reading = Reading.of(name, sub_index, modifiers, flags, sign)

    expected_parts = f"⟨{sign.get_key()}⟩" if sign else ""
    assert reading.value == expected_value
    assert reading.get_key() == f"Reading⁝{expected_value}{expected_parts}"
    assert reading.modifiers == tuple(modifiers)
    assert reading.flags == tuple(flags)
    assert reading.lemmatizable is False
    assert reading.sign == sign

    serialized = {
        "type": "Reading",
        "value": expected_value,
        "name": name,
        "subIndex": sub_index,
        "modifiers": modifiers,
        "flags": [flag.value for flag in flags],
        "sign": sign and dump_token(sign),
    }
    assert dump_token(reading) == serialized
    assert load_token(serialized) == reading


def test_load_old_style_reading():
    name = "kur"
    sub_index = 1
    flags = []
    modifiers = []
    sign = "KUR"
    reading = Reading.of(name, sub_index, modifiers, flags, ValueToken(sign))

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
    "name,sub_index,modifiers,flags,sign,surrogate,expected_value",
    [
        ("KUR", 1, [], [], None, [], "KUR"),
        ("KURʾ", 1, [], [], None, [], "KURʾ"),
        ("ʾ", 1, [], [], None, [], "ʾ"),
        ("KU[R", 1, [], [], None, [], "KU[R"),
        ("K]UR", 1, [], [], None, [], "K]UR"),
        ("KUR", 0, [], [], None, [], "KUR₀"),
        ("KUR", 1, [], [], Grapheme.of("KUR"), [], "KUR(KUR)"),
        (
            "KUR",
            1,
            [],
            [],
            None,
            [Reading.of("kur"), Joiner(atf.Joiner.HYPHEN), Reading.of("kur")],
            "KUR<(kur-kur)>",
        ),
        ("KUR", 1, ["@v", "@180"], [], None, [], "KUR@v@180"),
        ("KUR", 1, [], [atf.Flag.DAMAGE, atf.Flag.CORRECTION], None, [], "KUR#!"),
        (
            "KUR",
            10,
            ["@v"],
            [atf.Flag.CORRECTION],
            Grapheme.of("KUR"),
            [],
            "KUR₁₀@v!(KUR)",
        ),
    ],
)
def test_logogram(name, sub_index, modifiers, flags, sign, surrogate, expected_value):
    logogram = Logogram.of(name, sub_index, modifiers, flags, sign, surrogate)

    expected_parts = f"⟨{sign.get_key()}⟩" if sign else ""
    assert logogram.value == expected_value
    assert logogram.get_key() == f"Logogram⁝{expected_value}{expected_parts}"
    assert logogram.modifiers == tuple(modifiers)
    assert logogram.flags == tuple(flags)
    assert logogram.lemmatizable is False
    assert logogram.sign == sign
    assert logogram.surrogate == tuple(surrogate)

    serialized = {
        "type": "Logogram",
        "value": expected_value,
        "name": name,
        "subIndex": sub_index,
        "modifiers": modifiers,
        "flags": [flag.value for flag in flags],
        "surrogate": dump_tokens(surrogate),
        "sign": sign and dump_token(sign),
    }
    assert dump_token(logogram) == serialized
    assert load_token(serialized) == logogram


@pytest.mark.parametrize("name,sub_index", [("KUR", -1), ("kur", 1)])
@pytest.mark.skip
def test_invalid_logogram(name, sub_index):
    with pytest.raises(ValueError):
        Logogram.of(name, sub_index)


@pytest.mark.parametrize(
    "name,modifiers,flags,sign,expected_value",
    [
        ("1", [], [], None, "1"),
        ("1[4", [], [], None, "1[4"),
        ("1]0", [], [], None, "1]0"),
        ("1", [], [], Grapheme.of("KUR"), "1(KUR)"),
        ("1", ["@v", "@180"], [], None, "1@v@180"),
        ("1", [], [atf.Flag.DAMAGE, atf.Flag.CORRECTION], None, "1#!"),
        ("1", ["@v"], [atf.Flag.CORRECTION], Grapheme.of("KUR"), "1@v!(KUR)"),
    ],
)
def test_number(name, modifiers, flags, sign, expected_value):
    number = Number.of(name, modifiers, flags, sign)

    expected_sub_index = 1
    expected_parts = f"⟨{sign.get_key()}⟩" if sign else ""
    assert number.value == expected_value
    assert number.get_key() == f"Number⁝{expected_value}{expected_parts}"
    assert number.sub_index == expected_sub_index
    assert number.modifiers == tuple(modifiers)
    assert number.flags == tuple(flags)
    assert number.lemmatizable is False
    assert number.sign == sign

    serialized = {
        "type": "Number",
        "value": expected_value,
        "name": name,
        "modifiers": modifiers,
        "subIndex": expected_sub_index,
        "flags": [flag.value for flag in flags],
        "sign": sign and dump_token(sign),
    }
    assert dump_token(number) == serialized
    assert load_token(serialized) == number


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
    assert dump_token(compound) == serialized
    assert load_token(serialized) == compound


@pytest.mark.parametrize(
    "name,modifiers,flags,expected_value",
    [
        ("KUR12₁", [], [], "KUR12₁"),
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
    assert dump_token(grapheme) == serialized
    assert load_token(serialized) == grapheme
