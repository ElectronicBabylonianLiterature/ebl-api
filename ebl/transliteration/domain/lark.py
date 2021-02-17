from typing import Sequence

from lark.lexer import Token  # pyre-ignore[21]
from lark.tree import Tree  # pyre-ignore[21]

from ebl.transliteration.domain.tokens import Token as EblToken, ValueToken


def _token_to_list(token):
    if isinstance(token, Tree):
        return token.children
    elif isinstance(token, list):
        return token
    else:
        return [token]


def tokens_to_value_tokens(children: Sequence) -> Sequence[EblToken]:
    return tuple(
        (ValueToken.of(token.value) if isinstance(token, Token) else token)
        for child in children
        for token in _token_to_list(child)
    )
