import pytest

from ebl.transliteration.domain.enclosure_tokens import (
    Side,
    Erasure,
    DocumentOrientedGloss,
)
from ebl.transliteration.domain.token_schemas import dump_token, load_token


@pytest.mark.parametrize(
    "side, value", [(Side.LEFT, "°"), (Side.CENTER, "\\"), (Side.RIGHT, "°")]
)
def test_erasure(side, value):
    erasure = Erasure(side)

    assert erasure.value == value
    assert erasure.get_key() == f"Erasure⁝{value}"
    assert erasure.lemmatizable is False

    serialized = {
        "type": "Erasure",
        "value": erasure.value,
        "side": side.name,
    }
    assert dump_token(erasure) == serialized
    assert load_token(serialized) == erasure


@pytest.mark.parametrize("side", [Side.LEFT, Side.RIGHT])
def test_document_oriented_gloss(side):
    values = {Side.LEFT: "{(", Side.RIGHT: ")}"}
    value = values[side]
    gloss = DocumentOrientedGloss(value)
    equal = DocumentOrientedGloss(value)
    other = DocumentOrientedGloss(
        values[Side.LEFT if side == Side.RIGHT else Side.RIGHT]
    )

    assert gloss.value == value
    assert gloss.get_key() == f"DocumentOrientedGloss⁝{value}"
    assert gloss.side == side
    assert gloss.lemmatizable is False

    serialized = {
        "type": "DocumentOrientedGloss",
        "value": gloss.value,
    }
    assert dump_token(gloss) == serialized
    assert load_token(serialized) == gloss

    assert gloss == equal
    assert hash(gloss) == hash(equal)

    assert gloss != other
    assert hash(gloss) != hash(other)
