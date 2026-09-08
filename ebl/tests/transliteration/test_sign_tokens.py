from ebl.tests.asserts import assert_token_serialization
from ebl.transliteration.domain import atf as atf
from ebl.transliteration.domain.sign_tokens import (
    Divider,
)
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
