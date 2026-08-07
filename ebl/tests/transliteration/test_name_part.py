from typing import List

from ebl.transliteration.domain.enclosure_tokens import BrokenAway
from ebl.transliteration.domain.sign_token_base import NamePart
from ebl.transliteration.domain.tokens import Token, TokenVisitor, ValueToken


class RecordingVisitor(TokenVisitor):
    def __init__(self) -> None:
        self.visited: List[Token] = []

    def visit(self, token: Token) -> None:
        self.visited.append(token)


def test_a_value_token_contributes_its_text_to_the_name() -> None:
    part = NamePart.of(ValueToken.of("ku"))

    assert part.name_contribution == "ku"
    assert part.value == "ku"


def test_a_bracket_contributes_nothing_to_the_name() -> None:
    bracket = BrokenAway.open()
    part = NamePart.of(bracket)

    assert part.name_contribution == ""
    assert part.value == bracket.value


def test_parts_delegate_to_the_wrapped_token() -> None:
    token = ValueToken.of("ku")

    assert NamePart.of(token).parts == token.parts


def test_accept_delegates_to_the_wrapped_token() -> None:
    token = ValueToken.of("ku")
    visitor = RecordingVisitor()

    NamePart.of(token).accept(visitor)

    assert visitor.visited == [token]


def test_wrapping_is_idempotent() -> None:
    part = NamePart.of(ValueToken.of("ku"))

    assert NamePart.of(part).token is part
