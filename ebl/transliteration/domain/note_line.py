from typing import Sequence

import attr

from ebl.lemmatization.domain.lemmatization import LemmatizationToken
from ebl.transliteration.domain.atf import Atf
from ebl.transliteration.domain.line import Line
from ebl.transliteration.domain.markup import MarkupPart, convert_part_sequence


@attr.s(frozen=True, auto_attribs=True)
class NoteLine(Line):
    parts: Sequence[MarkupPart] = attr.ib(converter=convert_part_sequence)

    @property
    def key(self) -> str:
        parts = "⁚".join(part.key for part in self.parts)
        return f"NoteLine⁞{self.atf}⟨{parts}⟩"

    @property
    def atf(self) -> Atf:
        note = "".join(part.value for part in self.parts)
        return Atf(f"#note: {note}")

    @property
    def lemmatization(self) -> Sequence[LemmatizationToken]:
        return tuple(LemmatizationToken(part.value) for part in self.parts)
