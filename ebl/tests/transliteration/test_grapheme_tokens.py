import pytest

from ebl.tests.asserts import assert_token_serialization
from ebl.transliteration.domain import atf as atf
from ebl.transliteration.domain.sign import SignName
from ebl.transliteration.domain.sign_tokens import (
    CompoundGrapheme,
    Grapheme,
)


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
