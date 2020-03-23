from typing import Iterable, Tuple

from ebl.transliteration.domain import atf as atf
from ebl.transliteration.domain.tokens import Token


def convert_token_sequence(tokens: Iterable[Token]) -> Tuple[Token, ...]:
    return tuple(tokens)


def convert_string_sequence(strings: Iterable[str]) -> Tuple[str, ...]:
    return tuple(strings)


def convert_flag_sequence(flags: Iterable[atf.Flag]) -> Tuple[atf.Flag, ...]:
    return tuple(flags)
