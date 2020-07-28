from typing import Sequence

from ebl.transliteration.application.signs_visitor import SignsVisitor
from ebl.transliteration.domain.tokens import Token
from ebl.transliteration.domain.word_tokens import Word
from ebl.transliteration.domain.sign_tokens import Reading


def test_signs_visitor(sign_repository, signs):
    for sign in signs:
        sign_repository.create(sign)

    tokens: Sequence[Token] = [
        Word.of([Reading.of_name("ku")]),
        Word.of([Reading.of_name("gid", 2)]),
        Word.of([Reading.of_name("nu")]),
        Word.of([Reading.of_name("ši")]),
    ]

    visitor = SignsVisitor(sign_repository)
    for token in tokens:
        token.accept(visitor)

    assert visitor.result == ["KU", "BU", "ABZ075", "ABZ207a\\u002F207b\\u0020X"]
