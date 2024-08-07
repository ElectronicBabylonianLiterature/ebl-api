from typing import NewType, Optional, Sequence

import attr

from ebl.transliteration.domain.atf import Atf
from ebl.transliteration.domain.museum_number import MuseumNumber

SignName = NewType("SignName", str)


@attr.s(frozen=True, auto_attribs=True)
class SignListRecord:
    name: str
    number: str


@attr.s(frozen=True, auto_attribs=True)
class Value:
    value: str
    sub_index: Optional[int] = None


@attr.s(frozen=True, auto_attribs=True)
class Logogram:
    logogram: str = ""
    atf: Atf = Atf("")
    word_id: Sequence[str] = ()
    schramm_logogramme: str = ""
    unicode: str = ""


@attr.s(frozen=True, auto_attribs=True)
class Fossey:
    page: int = 0
    number: int = 0
    suffix: str = ""
    reference: str = ""
    new_edition: str = ""
    secondary_literature: str = ""
    cdli_number: str = ""
    museum_number: Optional[MuseumNumber] = None
    external_project: str = ""
    notes: str = ""
    date: str = ""
    transliteration: str = ""
    sign: str = ""


@attr.s(frozen=True, auto_attribs=True)
class SortKeys:
    neo_assyrian_onset: Sequence[int] = ()
    neo_babylonian_onset: Sequence[int] = ()
    neo_assyrian_offset: Sequence[int] = ()
    neo_babylonian_offset: Sequence[int] = ()


@attr.s(frozen=True, auto_attribs=True)
class Sign:
    name: SignName
    lists: Sequence[SignListRecord] = ()
    values: Sequence[Value] = ()
    mes_zl: str = ""
    labasi: str = ""
    reverse_order: str = ""
    logograms: Sequence[Logogram] = ()
    fossey: Sequence[Fossey] = ()
    unicode: Sequence[int] = ()
    sort_keys: Optional[SortKeys] = None

    @property
    def standardization(self):
        standardization_list = "ABZ"
        try:
            return [
                f"{record.name}{record.number}"
                for record in self.lists
                if record.name == standardization_list
            ][0]
        except IndexError:
            return self.name

    def set_logograms(self, logograms: Sequence[Logogram]) -> "Sign":
        return attr.evolve(self, logograms=tuple(logograms))
