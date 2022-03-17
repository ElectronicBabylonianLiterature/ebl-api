from functools import singledispatchmethod
from typing import Optional, TypeVar

import attr

from ebl.transliteration.domain.tokens import Token
from ebl.transliteration.domain.word_tokens import AbstractWord


class AlignmentError(Exception):
    def __init__(self, message: str = "Invalid alignment"):
        super().__init__(message)


T = TypeVar("T", bound=Token)
A = TypeVar("A", bound=AbstractWord)


@attr.s(auto_attribs=True, frozen=True)
class AlignmentToken:
    value: str
    alignment: Optional[int]
    variant: Optional[AbstractWord] = None

    @singledispatchmethod
    def apply(self, token: T) -> T:
        if (
            token.value == self.value
            and self.alignment is None
            and self.variant is None
        ):
            return token
        else:
            raise AlignmentError(f"Incompatible alignment {self} for token {token}.")

    @apply.register(AbstractWord)
    def _(self, token: A) -> A:
        if token.value == self.value and (token.alignable or self.alignment is None):
            return token.set_alignment(self.alignment, self.variant)
        else:
            raise AlignmentError(f"Incompatible alignment {self} for word {token}.")
