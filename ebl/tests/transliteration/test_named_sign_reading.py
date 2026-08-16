from typing import NamedTuple, Optional, Sequence, Tuple

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
from ebl.transliteration.domain.tokens import Token, ValueToken


class ReadingCase(NamedTuple):
    name_parts: Sequence[Token]
    sub_index: Optional[int]
    modifiers: Sequence[str]
    flags: Sequence[atf.Flag]
    sign: Optional[Token]
    expected_value: str
    expected_clean_value: str
    expected_name: str


CASES = [
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
]


@pytest.mark.parametrize("case", [ReadingCase(*case) for case in CASES])
def test_reading(case: ReadingCase) -> None:
    reading = Reading.of(
        case.name_parts, case.sub_index, case.modifiers, case.flags, case.sign
    )

    sign = case.sign
    expected_parts: Tuple[Token, ...] = tuple(case.name_parts) + (
        (sign,) if sign is not None else ()
    )
    assert reading.value == case.expected_value
    assert reading.clean_value == case.expected_clean_value
    assert (
        reading.get_key() == f"Reading⁝{case.expected_value}"
        f"⟨{'⁚'.join(token.get_key() for token in expected_parts)}⟩"
    )
    assert reading.name_tokens == tuple(case.name_parts)
    assert reading.name == case.expected_name
    assert reading.modifiers == tuple(case.modifiers)
    assert reading.flags == tuple(case.flags)
    assert reading.lemmatizable is False
    assert reading.sign == case.sign

    serialized = {
        "type": "Reading",
        "name": case.expected_name,
        "nameParts": OneOfTokenSchema().dump(case.name_parts, many=True),
        "subIndex": case.sub_index,
        "modifiers": case.modifiers,
        "flags": [flag.value for flag in case.flags],
        "sign": case.sign and OneOfTokenSchema().dump(case.sign),
    }
    assert_token_serialization(reading, serialized)
