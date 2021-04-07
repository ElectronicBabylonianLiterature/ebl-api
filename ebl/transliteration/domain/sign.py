from typing import NewType, Optional, Sequence

import attr

from ebl.transliteration.domain.atf import Atf

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
    word_id: Sequence[str] = tuple()
    schramm_logogramme: str = ""


@attr.s(frozen=True, auto_attribs=True)
class Sign:
    name: SignName
    lists: Sequence[SignListRecord] = tuple()
    values: Sequence[Value] = tuple()
    mes_zl: Optional[str] = None
    logograms: Sequence[Logogram] = tuple()

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
