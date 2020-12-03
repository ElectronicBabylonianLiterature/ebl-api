from typing import Optional, Sequence, TypeVar

import attr
from singledispatchmethod import singledispatchmethod  # pyre-ignore[21]

from ebl.transliteration.domain.tokens import Token
from ebl.transliteration.domain.word_tokens import AbstractWord
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.lark_parser import (
    parse_normalized_akkadian_word,
    parse_word,
)


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

    @singledispatchmethod  # pyre-ignore[56]
    def apply(self, token: T) -> T:
        if (
            token.value == self.value
            and self.alignment is None
            and self.variant is None
        ):
            return token
        else:
            raise AlignmentError(f"Incompatible alignment {self} for token {token}.")

    @apply.register(AbstractWord)  # pyre-ignore[56]
    def _(self, token: A) -> A:
        if token.value == self.value and (token.alignable or self.alignment is None):
            return token.set_alignment(self.alignment, self.variant)
        else:
            raise AlignmentError(f"Incompatible alignment {self} for word {token}.")

    @staticmethod
    def from_dict(data):
        return AlignmentToken(
            data["value"], data.get("alignment"), AlignmentToken._create_word(data)
        )

    @staticmethod
    def _create_word(data: dict) -> Optional[AbstractWord]:
        variant = data.get("variant")
        if variant:
            language = Language[data["language"]]
            is_normalized = data["isNormalized"]

            return (
                parse_normalized_akkadian_word(variant)
                if language is Language.AKKADIAN and is_normalized
                else parse_word(variant).set_language(language, is_normalized)
            )
        else:
            return None


@attr.s(auto_attribs=True, frozen=True)
class Alignment:
    _lines: Sequence[Sequence[Sequence[AlignmentToken]]]

    def get_line(self, line_index: int) -> Sequence[Sequence[AlignmentToken]]:
        return self._lines[line_index]

    def get_manuscript_line(
        self, line_index: int, manuscript_index: int
    ) -> Sequence[AlignmentToken]:
        return self.get_line(line_index)[manuscript_index]

    def get_number_of_lines(self) -> int:
        return len(self._lines)

    def get_number_of_manuscripts(self, line_index: int) -> int:
        return len(self.get_line(line_index))

    @staticmethod
    def from_dict(data):
        return Alignment(
            tuple(
                tuple(
                    tuple(AlignmentToken.from_dict(token) for token in manuscript)
                    for manuscript in line
                )
                for line in data
            )
        )
