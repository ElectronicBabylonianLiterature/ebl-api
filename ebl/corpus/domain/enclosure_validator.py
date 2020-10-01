from typing import Iterable

from ebl.transliteration.domain.reconstructed_text import ReconstructionToken
from ebl.transliteration.domain.enclosure_error import EnclosureError
from ebl.transliteration.domain.enclosure_visitor import EnclosureValidator


def validate(line: Iterable[ReconstructionToken]):
    try:
        visitor = EnclosureValidator()
        for token in line:
            token.accept(visitor)
        visitor.done()
    except EnclosureError as error:
        raise ValueError(f"Invalid line {[str(part) for part in line]}: " f"{error}")
