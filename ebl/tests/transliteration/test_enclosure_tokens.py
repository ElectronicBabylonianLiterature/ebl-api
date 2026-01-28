import pytest

from ebl.tests.asserts import assert_token_serialization
from ebl.transliteration.application.token_schemas import OneOfTokenSchema
from ebl.transliteration.domain.enclosure_tokens import (
    AccidentalOmission,
    Determinative,
    DocumentOrientedGloss,
    Emendation,
    Erasure,
    IntentionalOmission,
    LinguisticGloss,
    PhoneticGloss,
    Removal,
)
from ebl.transliteration.domain.side import Side
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.tokens import Joiner


@pytest.mark.parametrize(
    "enclosure_class, type_, sides",
    [
        (Erasure, "Erasure", {Side.LEFT: "°", Side.CENTER: "\\", Side.RIGHT: "°"}),
        (AccidentalOmission, "AccidentalOmission", {Side.LEFT: "<", Side.RIGHT: ">"}),
        (
            IntentionalOmission,
            "IntentionalOmission",
            {Side.LEFT: "<(", Side.RIGHT: ")>"},
        ),
        (Removal, "Removal", {Side.LEFT: "<<", Side.RIGHT: ">>"}),
        (Emendation, "Emendation", {Side.LEFT: "<", Side.RIGHT: ">"}),
        (
            DocumentOrientedGloss,
            "DocumentOrientedGloss",
            {Side.LEFT: "{(", Side.RIGHT: ")}"},
        ),
    ],
)
@pytest.mark.parametrize("side", [Side.LEFT, Side.RIGHT])
def test_enclosure(enclosure_class, type_, sides, side):
    value = sides[side]
    enclosure = enclosure_class.of(side)

    assert enclosure.value == value
    assert enclosure.clean_value == ""
    assert enclosure.get_key() == f"{type_}⁝{value}"
    assert enclosure.side == side
    assert enclosure.is_open == (side == Side.LEFT)
    assert enclosure.is_close == (side == Side.RIGHT)
    assert enclosure.lemmatizable is False

    serialized = {"type": type_, "side": side.name}
    assert_token_serialization(enclosure, serialized)


def test_determinative():
    parts = [Reading.of_name("kur"), Joiner.hyphen(), Reading.of_name("kur")]
    determinative = Determinative.of(parts)

    expected_value = f"{{{''.join(part.value for part in parts)}}}"
    expected_clean_value = f"{{{''.join(part.clean_value for part in parts)}}}"
    expected_parts = f"⟨{'⁚'.join(part.get_key() for part in parts)}⟩"
    assert determinative.value == expected_value
    assert determinative.clean_value == expected_clean_value
    assert determinative.get_key() == f"Determinative⁝{expected_value}{expected_parts}"
    assert determinative.parts == tuple(parts)
    assert determinative.lemmatizable is False

    serialized = {
        "type": "Determinative",
        "parts": OneOfTokenSchema().dump(parts, many=True),
    }
    assert_token_serialization(determinative, serialized)


def test_phonetic_gloss():
    parts = [Reading.of_name("kur"), Joiner.hyphen(), Reading.of_name("kur")]
    gloss = PhoneticGloss.of(parts)

    expected_value = f"{{+{''.join(part.value for part in parts)}}}"
    expected_clean_value = f"{{+{''.join(part.clean_value for part in parts)}}}"
    expected_parts = f"⟨{'⁚'.join(part.get_key() for part in parts)}⟩"
    assert gloss.value == expected_value
    assert gloss.clean_value == expected_clean_value
    assert gloss.get_key() == f"PhoneticGloss⁝{expected_value}{expected_parts}"
    assert gloss.parts == tuple(parts)
    assert gloss.lemmatizable is False

    serialized = {
        "type": "PhoneticGloss",
        "parts": OneOfTokenSchema().dump(parts, many=True),
    }
    assert_token_serialization(gloss, serialized)


def test_linguistic_gloss():
    parts = [Reading.of_name("kur"), Joiner.hyphen(), Reading.of_name("kur")]
    gloss = LinguisticGloss.of(parts)

    expected_value = f"{{{{{''.join(part.value for part in parts)}}}}}"
    expected_clean_value = f"{{{{{''.join(part.clean_value for part in parts)}}}}}"
    expected_parts = f"⟨{'⁚'.join(part.get_key() for part in parts)}⟩"
    assert gloss.value == expected_value
    assert gloss.clean_value == expected_clean_value
    assert gloss.get_key() == f"LinguisticGloss⁝{expected_value}{expected_parts}"
    assert gloss.parts == tuple(parts)
    assert gloss.lemmatizable is False

    serialized = {
        "type": "LinguisticGloss",
        "parts": OneOfTokenSchema().dump(parts, many=True),
    }
    assert_token_serialization(gloss, serialized)
