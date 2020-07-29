from typing import Sequence

import pytest  # pyre-ignore[21]

from ebl.transliteration.application.signs_visitor import SignsVisitor
from ebl.transliteration.domain.tokens import Token
from ebl.transliteration.domain.word_tokens import Word
from ebl.transliteration.domain.sign_tokens import CompoundGrapheme, Logogram, Reading


@pytest.mark.parametrize("tokens,expected",[
    (
        [
            Word.of([Reading.of_name("ku")]),
            Word.of([Reading.of_name("gid", 2)]),
            Word.of([Reading.of_name("nu")]),
            Word.of([Reading.of_name("ši")]),
        ],
        ["KU", "BU", "ABZ075", "ABZ207a\\u002F207b\\u0020X"]
    ),
    (
        [
            Word.of([CompoundGrapheme.of(["(4×ZA)×KUR"])]),
            Word.of([CompoundGrapheme.of(["(AŠ&AŠ@180)×U"])]),
            Word.of([Logogram.of_name("NU")]),
        ],
        ["ABZ531+588", "|(AŠ&AŠ@180)×U|", "ABZ075"]
    )
])
def test_signs_visitor(
    tokens: Sequence[Token],
    expected: Sequence[str],
    sign_repository, signs
):
    for sign in signs:
        sign_repository.create(sign)

    visitor = SignsVisitor(sign_repository)
    for token in tokens:
        token.accept(visitor)

    assert visitor.result == expected
