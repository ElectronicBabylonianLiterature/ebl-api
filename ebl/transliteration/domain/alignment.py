from typing import Optional, Sequence

import attr

from ebl.transliteration.domain import word_tokens
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.lark_parser import (
    parse_normalized_akkadian_word,
    parse_word,
)


class AlignmentError(Exception):
    def __init__(self):
        super().__init__("Invalid alignment")


@attr.s(auto_attribs=True, frozen=True)
class AlignmentToken:
    value: str
    alignment: Optional[int]
    variant: Optional["word_tokens.AbstractWord"] = None

    @staticmethod
    def from_dict(data):
        return AlignmentToken(
            data["value"], data.get("alignment"), AlignmentToken._create_word(data)
        )

    @staticmethod
    def _create_word(data: dict) -> Optional["word_tokens.AbstractWord"]:
        variant = data.get("variant")
        if variant:
            language = Language[data["language"]]
            is_normalized = data["isNormalized"]

            if language is Language.AKKADIAN and is_normalized:
                return parse_normalized_akkadian_word(variant)
            else:
                return parse_word(variant).set_language(language, is_normalized)
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
