from typing import List

import pytest

from ebl.dictionary.domain.word import WordId
from ebl.lemmatization.domain.lemmatization import (
    LemmatizationError,
    LemmatizationToken,
)
from ebl.transliteration.domain.enclosure_tokens import BrokenAway
from ebl.transliteration.domain.enclosure_type import EnclosureType
from ebl.transliteration.domain.sign_token_base import NamePart
from ebl.transliteration.domain.tokens import (
    ErasureState,
    Token,
    TokenVisitor,
    ValueToken,
)


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


def test_clean_value_delegates_to_the_wrapped_token() -> None:
    bracket = BrokenAway.open()

    assert NamePart.of(bracket).clean_value == bracket.clean_value == ""


def test_get_key_delegates_to_the_wrapped_token() -> None:
    bracket = BrokenAway.open()

    assert NamePart.of(bracket).get_key() == bracket.get_key()


def test_lemmatizable_delegates_to_the_wrapped_token() -> None:
    token = ValueToken.of("ku")

    assert NamePart.of(token).lemmatizable == token.lemmatizable


def test_alignable_delegates_to_the_wrapped_token() -> None:
    token = ValueToken.of("ku")

    assert NamePart.of(token).alignable == token.alignable


def test_set_unique_lemma_delegates_to_the_wrapped_token() -> None:
    token = ValueToken.of("ku")
    lemma = LemmatizationToken("ku")

    updated = NamePart.of(token).set_unique_lemma(lemma)

    assert updated.token == token.set_unique_lemma(lemma)


def test_set_unique_lemma_propagates_the_wrapped_token_error() -> None:
    part = NamePart.of(ValueToken.of("ku"))

    with pytest.raises(LemmatizationError):
        part.set_unique_lemma(LemmatizationToken("gid₂", (WordId("gid"),)))


def test_update_alignment_delegates_to_the_wrapped_token() -> None:
    token = ValueToken.of("ku")

    updated = NamePart.of(token).update_alignment([0])

    assert updated.token == token.update_alignment([0])


def test_set_enclosure_type_keeps_wrapper_and_token_in_step() -> None:
    enclosure = frozenset({EnclosureType.BROKEN_AWAY})

    part = NamePart.of(ValueToken.of("ku")).set_enclosure_type(enclosure)

    assert part.enclosure_type == enclosure
    assert part.token.enclosure_type == enclosure


def test_set_erasure_keeps_wrapper_and_token_in_step() -> None:
    part = NamePart.of(ValueToken.of("ku")).set_erasure(ErasureState.ERASED)

    assert part.erasure == ErasureState.ERASED
    assert part.token.erasure == ErasureState.ERASED


def test_merge_delegates_to_the_wrapped_token() -> None:
    new_token = ValueToken.of("gid₂")

    assert NamePart.of(ValueToken.of("ku")).merge(new_token) == new_token
