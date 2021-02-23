from typing import MutableSequence, Sequence

from lark.tree import Tree

from ebl.transliteration.domain.tokens import Token, TokenVisitor
from ebl.transliteration.domain.word_tokens import ErasureState


class ErasureVisitor(TokenVisitor):
    def __init__(self, state: ErasureState):
        self._tokens: MutableSequence[Token] = []
        self._state: ErasureState = state

    @property
    def tokens(self) -> Sequence[Token]:
        return tuple(self._tokens)

    def visit(self, token) -> None:
        self._tokens.append(token.set_erasure(self._state))


def set_erasure_state(tree: Tree, state: ErasureState) -> Sequence[Token]:
    visitor = ErasureVisitor(state)
    for child in tree.children:
        visitor.visit(child)
    return visitor.tokens
