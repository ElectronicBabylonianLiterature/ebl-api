from typing import Sequence

import attr

import ebl.transliteration.domain.atf as atf
from ebl.transliteration.domain.converters import convert_flag_sequence
from ebl.transliteration.domain.tokens import ErasureState, Token


GREEK_LETTERS: str = "ΑαΒβΓγΔδΕεΖζΗηΘθΙιΚκΛλΜμΝνΞξΟοΠπΡρΣσςΤτΥυΦφΧχΨψΩω"


@attr.s(auto_attribs=True, frozen=True)
class GreekLetter(Token):
    letter: str = attr.ib(validator=attr.validators.in_(GREEK_LETTERS))
    flags: Sequence[atf.Flag] = attr.ib(converter=convert_flag_sequence)

    @property
    def value(self) -> str:
        flags = "".join(flag.value for flag in self.flags)
        return f"{self.letter}{flags}"

    @property
    def clean_value(self) -> str:
        return self.letter

    @property
    def parts(self):
        return tuple()

    @staticmethod
    def of(letter: str, flags: Sequence[atf.Flag] = tuple()):
        return GreekLetter(frozenset(), ErasureState.NONE, letter, flags)
