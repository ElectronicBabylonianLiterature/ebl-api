from typing import List

import pytest

from ebl.transliteration.domain.tokens import Token, TokenVisitor, ValueToken


class RecordingVisitor(TokenVisitor):
    def __init__(self) -> None:
        self.visited: List[Token] = []

    def visit(self, token: Token) -> None:
        self.visited.append(token)


DELEGATING_METHODS = [
    "visit_word",
    "visit_language_shift",
    "visit_document_oriented_gloss",
    "visit_broken_away",
    "visit_perhaps_broken_away",
    "visit_accidental_omission",
    "visit_intentional_omission",
    "visit_removal",
    "visit_emendation",
    "visit_erasure",
    "visit_divider",
    "visit_egyptian_metrical_feet_separator",
    "visit_line_break",
    "visit_commentary_protocol",
    "visit_variant",
    "visit_gloss",
    "visit_named_sign",
    "visit_grapheme",
    "visit_compound_grapheme",
    "visit_unknown_sign",
    "visit_akkadian_word",
    "visit_greek_word",
    "visit_metrical_foot_separator",
    "visit_caesura",
]


@pytest.mark.parametrize("method_name", DELEGATING_METHODS)
def test_visit_methods_delegate_to_visit(method_name: str) -> None:
    visitor = RecordingVisitor()
    token = ValueToken.of("kur")

    getattr(visitor, method_name)(token)

    assert visitor.visited == [token]


def test_visit_number_delegates_through_visit_named_sign() -> None:
    class NamedSignRecordingVisitor(TokenVisitor):
        def __init__(self) -> None:
            self.named_signs: List[Token] = []

        def visit_named_sign(self, named_sign) -> None:
            self.named_signs.append(named_sign)

    visitor = NamedSignRecordingVisitor()
    token = ValueToken.of("kur")

    visitor.visit_number(token)

    assert visitor.named_signs == [token]


def test_base_visit_is_a_no_op() -> None:
    visitor = TokenVisitor()

    visitor.visit(ValueToken.of("kur"))

    assert not vars(visitor)


def test_update_alignment_returns_the_token_unchanged() -> None:
    token = ValueToken.of("kur")

    assert token.update_alignment({}) is token
