from typing import Sequence

import attr

from ebl.transliteration.domain import atf as atf
from ebl.transliteration.domain.converters import convert_flag_sequence
from ebl.transliteration.domain.tokens import ErasureState, Token, TokenVisitor


@attr.s(frozen=True, auto_attribs=True)
class EgyptianMetricalFeetSeparator(Token):
    flags: Sequence[atf.Flag] = attr.ib(default=(), converter=convert_flag_sequence)

    @property
    def clean_value(self) -> str:
        return self._sign

    @staticmethod
    def of(flags: Sequence[atf.Flag] = ()) -> "EgyptianMetricalFeetSeparator":
        return EgyptianMetricalFeetSeparator(frozenset(), ErasureState.NONE, flags)

    @property
    def parts(self):
        return ()

    @property
    def _sign(self) -> str:
        return atf.EGYPTIAN_METRICAL_FEET_SEPARATOR

    @property
    def string_flags(self) -> Sequence[str]:
        return [flag.value for flag in self.flags]

    @property
    def value(self) -> str:
        return f'{self._sign}{"".join(self.string_flags)}'

    def accept(self, visitor: TokenVisitor) -> None:
        visitor.visit_egyptian_metrical_feet_separator(self)
