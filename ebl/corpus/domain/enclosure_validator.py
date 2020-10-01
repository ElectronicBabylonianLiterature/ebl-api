from typing import Iterable

from ebl.corpus.domain.reconstructed_text import (
    AkkadianWord,
    Lacuna,
    ReconstructionToken,
)
from ebl.transliteration.domain.enclosure_error import EnclosureError
from ebl.transliteration.domain.enclosure_tokens import Emendation
from ebl.transliteration.domain.enclosure_visitor import EnclosureValidator
from ebl.transliteration.domain.enclosure_type import EnclosureType


class ReconstructionEnclosureValidator(EnclosureValidator):
    def visit_akkadian_word(self, word: AkkadianWord) -> None:
        for part in word.parts:
            part.accept(self)

    def visit_lacuna(self, lacuna: Lacuna) -> None:
        for enclosure in lacuna.parts:
            enclosure.accept(self)

    def visit_emendation(self, emendation: Emendation) -> None:
        self._update_state(emendation, EnclosureType.EMENDATION)


def validate(line: Iterable[ReconstructionToken]):
    try:
        visitor = ReconstructionEnclosureValidator()
        for token in line:
            token.accept(visitor)
        visitor.done()
    except EnclosureError as error:
        raise ValueError(f"Invalid line {[str(part) for part in line]}: " f"{error}")
