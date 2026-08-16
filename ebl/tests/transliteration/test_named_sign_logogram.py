from typing import NamedTuple, Optional, Sequence, Tuple

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
from ebl.transliteration.domain.tokens import Joiner, Token, ValueToken


class LogogramCase(NamedTuple):
    name_parts: Sequence[Token]
    sub_index: Optional[int]
    modifiers: Sequence[str]
    flags: Sequence[atf.Flag]
    sign: Optional[Token]
    surrogate: Sequence[Token]
    expected_value: str
    expected_clean_value: str
    expected_name: str


CASES = [
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
]


@pytest.mark.parametrize("case", [LogogramCase(*case) for case in CASES])
def test_logogram(case: LogogramCase) -> None:
    logogram = Logogram.of(
        case.name_parts, case.sub_index, case.modifiers, case.flags, case.sign
    ).with_surrogate(case.surrogate)

    sign = case.sign
    expected_parts: Tuple[Token, ...] = tuple(case.name_parts) + (
        (sign,) if sign is not None else ()
    )
    assert logogram.value == case.expected_value
    assert logogram.clean_value == case.expected_clean_value
    assert (
        logogram.get_key() == f"Logogram⁝{case.expected_value}"
        f"⟨{'⁚'.join(token.get_key() for token in expected_parts)}⟩"
    )
    assert logogram.name_tokens == tuple(case.name_parts)
    assert logogram.name == case.expected_name
    assert logogram.modifiers == tuple(case.modifiers)
    assert logogram.flags == tuple(case.flags)
    assert logogram.lemmatizable is False
    assert logogram.sign == case.sign
    assert logogram.surrogate == tuple(case.surrogate)

    serialized = {
        "type": "Logogram",
        "name": case.expected_name,
        "nameParts": OneOfTokenSchema().dump(case.name_parts, many=True),
        "subIndex": case.sub_index,
        "modifiers": case.modifiers,
        "flags": [flag.value for flag in case.flags],
        "surrogate": OneOfTokenSchema().dump(case.surrogate, many=True),
        "sign": case.sign and OneOfTokenSchema().dump(case.sign),
    }
    assert_token_serialization(logogram, serialized)
